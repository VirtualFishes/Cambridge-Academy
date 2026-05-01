"""
Servicio de notas y registro académico.

Coordina las reglas de aplicación para registrar, consultar y modificar notas.
La capa models conserva las consultas SQL; este servicio valida permisos,
contexto académico y calcula promedio/estado antes de persistir.
"""

from ca_program.entities.fixed_values import AcademicStatus
from ca_program.models.course_model import CourseModel
from ca_program.models.enrollment_model import EnrollmentModel
from ca_program.models.grade_model import GradeModel
from ca_program.models.professor_model import ProfessorModel
from ca_program.models.student_model import StudentModel
from ca_program.services import service_utils as utils
from database.connection import get_connection


class GradeService:
    """Servicio para gestionar registro académico de notas."""

    MIN_GRADE = 0.0
    MAX_GRADE = 5.0
    PASSING_GRADE = 3.0

    @staticmethod
    def get_students_for_grade_registration(
        user=None,
        id_user: int | str | None = None,
        code_course: int | str | None = None,
    ) -> dict:
        """
        Consulta estudiantes con inscripción confirmada en un curso del profesor.

        Soporta HU-26: solo entrega estudiantes de cursos asignados al profesor
        autenticado y con matrícula confirmada mediante recibo pagado.
        """
        connection = None
        cursor = None

        try:
            GradeService._require_professor_role(user)
            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)
            clean_code_course = GradeService._validate_code_course(code_course)

            connection = get_connection()
            cursor = connection.cursor()

            professor = GradeService._get_professor_by_user_id_with_cursor(cursor, clean_id_user)
            if professor is None:
                return GradeService._response(
                    success=False,
                    message="No existe un perfil de profesor asociado a este usuario.",
                    students=[],
                    enrollments=[],
                )

            course = GradeService._get_assigned_course_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
                id_professor=professor.id_professor,
            )
            if course is None:
                return GradeService._response(
                    success=False,
                    message="Curso no encontrado o no asignado al profesor autenticado.",
                    professor=professor,
                    students=[],
                    enrollments=[],
                )

            enrollments = EnrollmentModel.get_confirmed_enrollments_by_course_and_professor_id_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
                id_professor=professor.id_professor,
            )

            student_records = [
                GradeService._enrollment_to_dict(
                    enrollment=enrollment,
                    grade=GradeModel.get_grade_by_enrollment_id_with_cursor(
                        cursor=cursor,
                        id_enrollment=enrollment.id_enrollment,
                    ),
                )
                for enrollment in enrollments
            ]

            return GradeService._response(
                success=True,
                message="Estudiantes del curso consultados correctamente.",
                professor=professor,
                course=course,
                students=student_records,
                enrollments=enrollments,
                data=student_records,
            )

        except ValueError as exc:
            return GradeService._response(success=False, message=str(exc), students=[], enrollments=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los estudiantes para registrar notas.",
                students=[],
                enrollments=[],
            )
        finally:
            GradeService._close_resources(cursor, connection)

    @staticmethod
    def register_grade_for_student(
        user=None,
        id_user: int | str | None = None,
        code_course: int | str | None = None,
        id_enrollment: int | str | None = None,
        grade1: int | float | str | None = None,
        grade2: int | float | str | None = None,
        grade3: int | float | str | None = None,
    ) -> dict:
        """
        Registra notas de una matrícula confirmada.

        Calcula promedio y estado en el servicio, y evita duplicar notas para la
        misma matrícula. La transacción cubre validación contextual y creación.
        """
        connection = None
        cursor = None

        try:
            GradeService._require_professor_role(user)
            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)
            clean_code_course = GradeService._validate_code_course(code_course)
            clean_id_enrollment = GradeService._validate_positive_int(id_enrollment, "La matrícula del estudiante es obligatoria.", "La matrícula del estudiante no es válida.")
            clean_grade1, clean_grade2, clean_grade3 = GradeService._validate_grades(grade1, grade2, grade3)
            average = GradeService._calculate_average(clean_grade1, clean_grade2, clean_grade3)
            status = GradeService._calculate_status(average)

            connection = get_connection()
            cursor = connection.cursor()

            professor, course, enrollment = GradeService._resolve_grade_context(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
                id_enrollment=clean_id_enrollment,
            )

            existing_grade = GradeModel.get_grade_by_enrollment_id_with_cursor(
                cursor=cursor,
                id_enrollment=clean_id_enrollment,
            )
            if existing_grade is not None:
                connection.rollback()
                return GradeService._response(
                    success=False,
                    message=(
                        "Este estudiante ya tiene notas registradas para el curso. "
                        "La modificación corresponde a la HU-28."
                    ),
                    professor=professor,
                    course=course,
                    grade=existing_grade,
                    data=GradeService._grade_to_dict(existing_grade),
                )

            grade = GradeModel.create_grade(
                cursor=cursor,
                id_enrollment=enrollment.id_enrollment,
                grade1=clean_grade1,
                grade2=clean_grade2,
                grade3=clean_grade3,
                average=average,
                status=status,
            )

            connection.commit()
            grade_record = GradeService._grade_to_dict(grade)
            return GradeService._response(
                success=True,
                message="Notas registradas correctamente.",
                professor=professor,
                course=course,
                grade=grade,
                data=grade_record,
            )

        except ValueError as exc:
            GradeService._rollback(connection)
            return GradeService._response(success=False, message=str(exc))
        except Exception as exc:
            GradeService._rollback(connection)
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al registrar las notas del estudiante.",
            )
        finally:
            GradeService._close_resources(cursor, connection)

    @staticmethod
    def get_grade_record_by_course_for_user(
        user=None,
        id_user: int | str | None = None,
        code_course: int | str | None = None,
    ) -> dict:
        """
        Consulta la planilla de notas de un curso asignado al profesor.

        Soporta HU-27 y conserva la restricción de consultar únicamente cursos
        del profesor autenticado.
        """
        connection = None
        cursor = None

        try:
            GradeService._require_professor_role(user)
            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)
            clean_code_course = GradeService._validate_code_course(code_course)

            connection = get_connection()
            cursor = connection.cursor()

            professor = GradeService._get_professor_by_user_id_with_cursor(cursor, clean_id_user)
            if professor is None:
                return GradeService._response(
                    success=False,
                    message="No existe un perfil de profesor asociado a este usuario.",
                    grades=[],
                    summary=GradeService._empty_grade_summary(),
                )

            course = GradeService._get_assigned_course_with_cursor(cursor, clean_code_course, professor.id_professor)
            if course is None:
                return GradeService._response(
                    success=False,
                    message="Curso no encontrado o no asignado al profesor autenticado.",
                    professor=professor,
                    grades=[],
                    summary=GradeService._empty_grade_summary(),
                )

            confirmed_enrollments = EnrollmentModel.get_confirmed_enrollments_by_course_and_professor_id_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
                id_professor=professor.id_professor,
            )
            grade_entities = GradeModel.get_grades_by_course_and_professor_id_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
                id_professor=professor.id_professor,
            )
            grade_records = [GradeService._grade_to_dict(grade) for grade in grade_entities]
            summary = GradeService._build_grade_record_summary(grade_entities, confirmed_enrollments)

            return GradeService._response(
                success=True,
                message="Registro de notas consultado correctamente.",
                professor=professor,
                course=course,
                grades=grade_records,
                grade_entities=grade_entities,
                summary=summary,
                data=grade_records,
            )

        except ValueError as exc:
            return GradeService._response(success=False, message=str(exc), grades=[], summary=GradeService._empty_grade_summary())
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el registro de notas del curso.",
                grades=[],
                summary=GradeService._empty_grade_summary(),
            )
        finally:
            GradeService._close_resources(cursor, connection)

    @staticmethod
    def update_grade_for_student(
        user=None,
        id_user: int | str | None = None,
        code_course: int | str | None = None,
        id_grade: int | str | None = None,
        grade1: int | float | str | None = None,
        grade2: int | float | str | None = None,
        grade3: int | float | str | None = None,
    ) -> dict:
        """
        Modifica notas existentes de un estudiante en un curso asignado.

        Soporta HU-28. Recalcula promedio y estado académico antes de guardar.
        """
        connection = None
        cursor = None

        try:
            GradeService._require_professor_role(user)
            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)
            clean_code_course = GradeService._validate_code_course(code_course)
            clean_id_grade = GradeService._validate_positive_int(id_grade, "El identificador de la nota es obligatorio.", "El identificador de la nota no es válido.")
            clean_grade1, clean_grade2, clean_grade3 = GradeService._validate_grades(grade1, grade2, grade3)
            average = GradeService._calculate_average(clean_grade1, clean_grade2, clean_grade3)
            status = GradeService._calculate_status(average)

            connection = get_connection()
            cursor = connection.cursor()

            professor = GradeService._get_professor_by_user_id_with_cursor(cursor, clean_id_user)
            if professor is None:
                connection.rollback()
                return GradeService._response(success=False, message="No existe un perfil de profesor asociado a este usuario.")

            course = GradeService._get_assigned_course_with_cursor(cursor, clean_code_course, professor.id_professor)
            if course is None:
                connection.rollback()
                return GradeService._response(
                    success=False,
                    message="Curso no encontrado o no asignado al profesor autenticado.",
                    professor=professor,
                )

            existing_grade = GradeModel.get_grade_by_id_course_and_professor_id(
                cursor=cursor,
                id_grade=clean_id_grade,
                code_course=clean_code_course,
                id_professor=professor.id_professor,
            )
            if existing_grade is None:
                connection.rollback()
                return GradeService._response(
                    success=False,
                    message=(
                        "La nota seleccionada no existe, no pertenece a este curso "
                        "o no corresponde al profesor autenticado."
                    ),
                    professor=professor,
                    course=course,
                )

            updated_grade = GradeModel.update_grade(
                cursor=cursor,
                id_grade=clean_id_grade,
                grade1=clean_grade1,
                grade2=clean_grade2,
                grade3=clean_grade3,
                average=average,
                status=status,
            )

            connection.commit()
            grade_record = GradeService._grade_to_dict(updated_grade)
            return GradeService._response(
                success=True,
                message="Notas modificadas correctamente.",
                professor=professor,
                course=course,
                grade=updated_grade,
                data=grade_record,
            )

        except ValueError as exc:
            GradeService._rollback(connection)
            return GradeService._response(success=False, message=str(exc))
        except Exception as exc:
            GradeService._rollback(connection)
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al modificar las notas del estudiante.",
            )
        finally:
            GradeService._close_resources(cursor, connection)

    @staticmethod
    def get_student_grade_record(user=None, id_user: int | str | None = None) -> dict:
        """
        Consulta el registro de notas del estudiante autenticado.

        Soporta HU-23. Usa el usuario autenticado para impedir consultas de
        notas ajenas.
        """
        connection = None
        cursor = None

        try:
            GradeService._require_student_role(user)
            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)

            connection = get_connection()
            cursor = connection.cursor()

            student = GradeService._get_student_by_user_id_with_cursor(cursor, clean_id_user)
            if student is None:
                return GradeService._response(
                    success=False,
                    message="No existe un perfil de estudiante asociado a este usuario.",
                    grades=[],
                    summary=GradeService._empty_student_grade_summary(),
                )

            raw_records = GradeService._get_student_grade_records_with_cursor(
                cursor=cursor,
                id_student=student.id_student,
            )
            grade_records = [GradeService._student_grade_record_to_dict(record) for record in (raw_records or [])]
            summary = GradeService._build_student_grade_summary(grade_records)

            return GradeService._response(
                success=True,
                message="Registro de notas del estudiante consultado correctamente.",
                student=student,
                grades=grade_records,
                summary=summary,
                data=grade_records,
            )

        except ValueError as exc:
            return GradeService._response(success=False, message=str(exc), grades=[], summary=GradeService._empty_student_grade_summary())
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar las notas del estudiante.",
                grades=[],
                summary=GradeService._empty_student_grade_summary(),
            )
        finally:
            GradeService._close_resources(cursor, connection)

    @staticmethod
    def search_students_for_admin(search_text: str | None = None, user=None) -> dict:
        """Busca estudiantes disponibles para consulta académica administrativa."""
        try:
            GradeService._require_admin_role(user)
            students = StudentModel.search_students(search_text)
            student_records = [utils.student_to_dict(student) for student in students]

            return GradeService._response(
                success=True,
                message="Estudiantes consultados correctamente.",
                students=student_records,
                data=student_records,
            )

        except ValueError as exc:
            return GradeService._response(success=False, message=str(exc), students=[], data=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los estudiantes.",
                students=[],
                data=[],
            )

    @staticmethod
    def get_student_grade_record_for_admin(id_student: int | str | None = None, user=None) -> dict:
        """
        Consulta el registro académico de un estudiante seleccionado por administración.

        Soporta HU-17 y no modifica notas; únicamente centraliza una consulta de
        lectura con validación de rol administrativo.
        """
        connection = None
        cursor = None

        try:
            GradeService._require_admin_role(user)
            clean_id_student = GradeService._validate_id_student(id_student)

            connection = get_connection()
            cursor = connection.cursor()

            student_lookup = getattr(StudentModel, "get_student_by_id_with_cursor", None)
            student = (
                student_lookup(cursor=cursor, id_student=clean_id_student)
                if student_lookup
                else StudentModel.get_student_by_id(clean_id_student)
            )
            if student is None:
                return GradeService._response(
                    success=False,
                    message="El estudiante seleccionado no existe.",
                    grades=[],
                    summary=GradeService._empty_admin_student_grade_summary(),
                )

            grade_lookup = getattr(GradeModel, "get_grade_records_by_student_id_for_admin_with_cursor", None)
            raw_records = (
                grade_lookup(cursor=cursor, id_student=student.id_student)
                if grade_lookup
                else GradeModel.get_grade_records_by_student_id_for_admin(id_student=student.id_student)
            )
            grade_records = [GradeService._student_grade_record_to_dict(record) for record in (raw_records or [])]
            summary = GradeService._build_admin_student_grade_summary(grade_records)

            return GradeService._response(
                success=True,
                message="Registro académico del estudiante consultado correctamente.",
                student=student,
                grades=grade_records,
                summary=summary,
                data=grade_records,
            )

        except ValueError as exc:
            return GradeService._response(success=False, message=str(exc), grades=[], summary=GradeService._empty_admin_student_grade_summary())
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el registro académico del estudiante.",
                grades=[],
                summary=GradeService._empty_admin_student_grade_summary(),
            )
        finally:
            GradeService._close_resources(cursor, connection)

    @staticmethod
    def _resolve_grade_context(cursor, id_user: int, code_course: str, id_enrollment: int):
        """Resuelve profesor, curso y matrícula validando pertenencia y pago."""
        professor = GradeService._get_professor_by_user_id_with_cursor(cursor, id_user)
        if professor is None:
            raise ValueError("No existe un perfil de profesor asociado a este usuario.")

        course = GradeService._get_assigned_course_with_cursor(cursor, code_course, professor.id_professor)
        if course is None:
            raise ValueError("Curso no encontrado o no asignado al profesor autenticado.")

        enrollment = EnrollmentModel.get_confirmed_enrollment_by_id_course_and_professor_id(
            cursor=cursor,
            id_enrollment=id_enrollment,
            code_course=code_course,
            id_professor=professor.id_professor,
        )
        if enrollment is None:
            raise ValueError(
                "La matrícula seleccionada no existe, no pertenece a este curso "
                "o no tiene inscripción confirmada."
            )

        return professor, course, enrollment

    @staticmethod
    def _get_student_grade_records_with_cursor(cursor, id_student: str):
        """Consulta registros académicos de estudiante usando cursor si el modelo lo soporta."""
        grade_lookup = getattr(GradeModel, "get_grade_records_by_student_id_with_cursor", None)
        if grade_lookup:
            return grade_lookup(cursor=cursor, id_student=id_student)
        return GradeModel.get_grade_records_by_student_id(id_student=id_student)

    @staticmethod
    def _empty_grade_summary() -> dict:
        return {
            "total_confirmed": 0,
            "total_graded": 0,
            "graded": 0,
            "approved": 0,
            "failed": 0,
            "pending": 0,
            "course_average": 0.0,
            "approval_rate": 0.0,
            "failure_rate": 0.0,
        }

    @staticmethod
    def _build_grade_record_summary(grades: list, confirmed_enrollments: list) -> dict:
        """Calcula resumen de una planilla de notas por curso."""
        total_confirmed = len(confirmed_enrollments or [])
        unique_graded_enrollments = set()
        approved = 0
        failed = 0
        average_sum = 0.0

        for grade in grades or []:
            enrollment = getattr(grade, "enrollment", None)
            id_enrollment = getattr(enrollment, "id_enrollment", None)
            if id_enrollment not in (None, ""):
                unique_graded_enrollments.add(id_enrollment)

            status_value = utils.status_to_value(getattr(grade, "status", ""))
            if status_value == AcademicStatus.PASSED.value:
                approved += 1
            elif status_value == AcademicStatus.FAILED.value:
                failed += 1

            average_sum += GradeService._safe_float(getattr(grade, "average", 0))

        total_graded = len(unique_graded_enrollments) if unique_graded_enrollments else len(grades or [])
        pending = max(total_confirmed - total_graded, 0)
        course_average = round(average_sum / total_graded, 2) if total_graded else 0.0

        return {
            "total_confirmed": total_confirmed,
            "total_graded": total_graded,
            "graded": total_graded,
            "approved": approved,
            "failed": failed,
            "pending": pending,
            "course_average": course_average,
            "approval_rate": round((approved / total_graded) * 100, 2) if total_graded else 0.0,
            "failure_rate": round((failed / total_graded) * 100, 2) if total_graded else 0.0,
        }

    @staticmethod
    def _empty_student_grade_summary() -> dict:
        return {
            "total_courses": 0,
            "total_enrolled": 0,
            "total_graded": 0,
            "graded": 0,
            "approved": 0,
            "failed": 0,
            "pending": 0,
            "general_average": 0.0,
            "academic_average": 0.0,
            "approval_rate": 0.0,
            "failure_rate": 0.0,
        }

    @staticmethod
    def _build_student_grade_summary(records: list[dict]) -> dict:
        """Calcula resumen académico de un estudiante."""
        total_courses = len(records or [])
        graded_records = [record for record in (records or []) if record.get("has_grade")]
        total_graded = len(graded_records)
        approved = 0
        failed = 0
        average_sum = 0.0

        for record in graded_records:
            status_value = utils.status_to_value(record.get("status", ""))
            if status_value == AcademicStatus.PASSED.value:
                approved += 1
            elif status_value == AcademicStatus.FAILED.value:
                failed += 1
            average_sum += GradeService._safe_float(record.get("average", 0))

        pending = max(total_courses - total_graded, 0)
        general_average = round(average_sum / total_graded, 2) if total_graded else 0.0

        return {
            "total_courses": total_courses,
            "total_enrolled": total_courses,
            "total_graded": total_graded,
            "graded": total_graded,
            "approved": approved,
            "failed": failed,
            "pending": pending,
            "general_average": general_average,
            "academic_average": general_average,
            "approval_rate": round((approved / total_graded) * 100, 2) if total_graded else 0.0,
            "failure_rate": round((failed / total_graded) * 100, 2) if total_graded else 0.0,
        }

    @staticmethod
    def _empty_admin_student_grade_summary() -> dict:
        summary = GradeService._empty_student_grade_summary()
        summary.update({"confirmed_courses": 0, "graded_courses": 0, "pending_courses": 0})
        return summary

    @staticmethod
    def _build_admin_student_grade_summary(records: list[dict]) -> dict:
        summary = GradeService._build_student_grade_summary(records)
        summary.update(
            {
                "confirmed_courses": summary.get("total_courses", 0),
                "graded_courses": summary.get("total_graded", 0),
                "pending_courses": summary.get("pending", 0),
            }
        )
        return summary

    @staticmethod
    def _get_professor_by_user_id_with_cursor(cursor, id_user: int):
        lookup = getattr(ProfessorModel, "_get_professor_by_user_id_with_cursor", None)
        if lookup:
            return lookup(cursor=cursor, id_user=id_user)
        return ProfessorModel.get_professor_by_user_id(id_user)

    @staticmethod
    def _get_student_by_user_id_with_cursor(cursor, id_user: int):
        lookup = getattr(StudentModel, "_get_student_by_user_id_with_cursor", None)
        if lookup:
            return lookup(cursor=cursor, id_user=id_user)
        return StudentModel.get_student_by_user_id(id_user)

    @staticmethod
    def _get_assigned_course_with_cursor(cursor, code_course: int | str, id_professor: int | str):
        lookup = getattr(CourseModel, "_get_course_by_code_and_professor_id_with_cursor", None)
        if lookup:
            return lookup(cursor=cursor, code_course=code_course, id_professor=id_professor)
        return CourseModel.get_course_by_code_and_professor_id(code_course=code_course, id_professor=id_professor)

    @staticmethod
    def _require_professor_role(user) -> None:
        if not utils.role_matches(user, {"professor"}, allow_missing=True):
            raise ValueError("El usuario autenticado no tiene permisos de profesor.")

    @staticmethod
    def _require_student_role(user) -> None:
        if not utils.role_matches(user, {"student"}, allow_missing=True):
            raise ValueError("El usuario autenticado no tiene permisos de estudiante.")

    @staticmethod
    def _require_admin_role(user) -> None:
        if not utils.role_matches(user, {"admin", "administrator"}, allow_missing=True):
            raise ValueError("El usuario autenticado no tiene permisos administrativos.")

    @staticmethod
    def _validate_id_student(id_student: int | str | None) -> str:
        return utils.clean_text(id_student, "El estudiante", min_length=1)

    @staticmethod
    def _validate_code_course(code_course: int | str | None) -> str:
        return utils.clean_text(code_course, "El código del curso", min_length=1)

    @staticmethod
    def _validate_positive_int(value, required_message: str, invalid_message: str) -> int:
        if value in (None, ""):
            raise ValueError(required_message)
        try:
            clean_value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(invalid_message) from exc
        if clean_value <= 0:
            raise ValueError(invalid_message)
        return clean_value

    @staticmethod
    def _validate_grade(value, label: str) -> float:
        if value in (None, ""):
            raise ValueError(f"{label} es obligatoria.")

        grade = utils.parse_float(value, f"{label} debe ser un número válido.")
        if grade < GradeService.MIN_GRADE or grade > GradeService.MAX_GRADE:
            raise ValueError(
                f"{label} debe estar entre {GradeService.MIN_GRADE:.1f} "
                f"y {GradeService.MAX_GRADE:.1f}."
            )
        return round(grade, 2)

    @staticmethod
    def _validate_grades(grade1, grade2, grade3) -> tuple[float, float, float]:
        return (
            GradeService._validate_grade(grade1, "Nota 1"),
            GradeService._validate_grade(grade2, "Nota 2"),
            GradeService._validate_grade(grade3, "Nota 3"),
        )

    @staticmethod
    def _calculate_average(grade1: float, grade2: float, grade3: float) -> float:
        return round((grade1 + grade2 + grade3) / 3, 2)

    @staticmethod
    def _calculate_status(average: float) -> AcademicStatus:
        return AcademicStatus.PASSED if average >= GradeService.PASSING_GRADE else AcademicStatus.FAILED

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _response(
        success: bool,
        message: str,
        professor=None,
        student=None,
        course=None,
        students: list[dict] | None = None,
        enrollments: list | None = None,
        grade=None,
        grades: list[dict] | None = None,
        grade_entities: list | None = None,
        summary: dict | None = None,
        data=None,
    ) -> dict:
        """Construye respuestas compatibles con la GUI existente."""
        response = {"success": success, "message": message}

        if professor is not None:
            response["professor"] = professor
            response["professor_data"] = utils.professor_to_dict(professor)
        if student is not None:
            response["student"] = student
            response["student_data"] = utils.student_to_dict(student)
        if course is not None:
            response["course"] = utils.course_to_dict(course)
            response["course_entity"] = course
        if students is not None:
            response["students"] = students
        if enrollments is not None:
            response["enrollments"] = enrollments
            response["entities"] = enrollments
        if grade is not None:
            response["grade"] = GradeService._grade_to_dict(grade)
            response["grade_entity"] = grade
        if grades is not None:
            response["grades"] = grades
            response["grade_records"] = grades
        if grade_entities is not None:
            response["grade_entities"] = grade_entities
        if summary is not None:
            response["summary"] = summary
        if data is not None:
            response["data"] = data

        return response

    @staticmethod
    def _enrollment_to_dict(enrollment, grade=None) -> dict:
        grade_record = GradeService._grade_to_dict(grade) if grade is not None else None
        return {
            "id_enrollment": getattr(enrollment, "id_enrollment", ""),
            "student": utils.student_to_dict(getattr(enrollment, "student", None)),
            "course": utils.course_to_dict(getattr(enrollment, "course", None)),
            "has_grade": grade_record is not None,
            "can_register": grade_record is None,
            "grade": grade_record,
        }

    @staticmethod
    def _student_grade_record_to_dict(record) -> dict:
        """Convierte registros de GradeModel a diccionarios de solo lectura."""
        if isinstance(record, dict):
            enrollment = record.get("enrollment")
            grade = record.get("grade")
        else:
            enrollment = getattr(record, "enrollment", None)
            grade = record if enrollment is not None and hasattr(record, "grade1") else getattr(record, "grade", None)

        if grade is not None:
            grade_data = GradeService._grade_to_dict(grade)
            course_data = grade_data.get("course", {})
            return {
                "id_enrollment": grade_data.get("id_enrollment", getattr(enrollment, "id_enrollment", "")),
                "id_grade": grade_data.get("id_grade", ""),
                "student": grade_data.get("student", {}),
                "course": course_data,
                "code_course": grade_data.get("code_course", course_data.get("code_course", "")),
                "course_name": grade_data.get("course_name", course_data.get("name", "")),
                "professor": course_data.get("professor", {}),
                "professor_name": course_data.get("professor", {}).get("name", ""),
                "has_grade": True,
                "grade1": grade_data.get("grade1", 0),
                "grade2": grade_data.get("grade2", 0),
                "grade3": grade_data.get("grade3", 0),
                "average": grade_data.get("average", 0),
                "status": grade_data.get("status", ""),
                "status_label": grade_data.get("status_label", "Sin estado"),
                "grade": grade_data,
            }

        enrollment_data = utils.enrollment_to_dict(enrollment) if enrollment is not None else {}
        course_data = enrollment_data.get("course", {})
        return {
            "id_enrollment": enrollment_data.get("id_enrollment", ""),
            "id_grade": "",
            "student": enrollment_data.get("student", {}),
            "course": course_data,
            "code_course": course_data.get("code_course", ""),
            "course_name": course_data.get("name", ""),
            "professor": course_data.get("professor", {}),
            "professor_name": course_data.get("professor", {}).get("name", ""),
            "has_grade": False,
            "grade1": "",
            "grade2": "",
            "grade3": "",
            "average": "",
            "status": "pending",
            "status_label": "Pendiente",
            "grade": None,
        }

    @staticmethod
    def _grade_to_dict(grade) -> dict:
        enrollment = getattr(grade, "enrollment", None)
        student = getattr(enrollment, "student", None)
        course = getattr(enrollment, "course", None)
        status = getattr(grade, "status", "")
        student_data = utils.student_to_dict(student)
        course_data = utils.course_to_dict(course)
        average = getattr(grade, "average", 0)

        return {
            "id_grade": getattr(grade, "id_grade", ""),
            "id_enrollment": getattr(enrollment, "id_enrollment", ""),
            "id_student": student_data.get("id_student", ""),
            "student_name": student_data.get("name", ""),
            "student_email": student_data.get("email", ""),
            "code_course": course_data.get("code_course", ""),
            "course_name": course_data.get("name", ""),
            "student": student_data,
            "course": course_data,
            "grade1": getattr(grade, "grade1", 0),
            "grade2": getattr(grade, "grade2", 0),
            "grade3": getattr(grade, "grade3", 0),
            "average": average,
            "status": utils.status_to_value(status),
            "status_name": getattr(status, "name", str(status)).lower(),
            "status_label": utils.academic_status_to_label(status),
        }

    @staticmethod
    def _rollback(connection) -> None:
        if connection:
            connection.rollback()

    @staticmethod
    def _close_resources(cursor, connection) -> None:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    _status_to_value = staticmethod(utils.status_to_value)
    _status_to_label = staticmethod(utils.academic_status_to_label)
    _professor_to_dict = staticmethod(utils.professor_to_dict)
    _course_to_dict = staticmethod(utils.course_to_dict)
    _student_to_dict = staticmethod(utils.student_to_dict)

    get_admin_students_for_grade_record = search_students_for_admin
    list_students_for_admin_grade_record = search_students_for_admin
    search_students_for_grade_record_admin = search_students_for_admin

    get_admin_student_grade_record = get_student_grade_record_for_admin
    get_student_academic_record_for_admin = get_student_grade_record_for_admin
    get_admin_grade_record_by_student = get_student_grade_record_for_admin
    consult_student_grade_record_for_admin = get_student_grade_record_for_admin
    consult_admin_student_grade_record = get_student_grade_record_for_admin
    list_student_grade_record_for_admin = get_student_grade_record_for_admin

    get_student_grades = get_student_grade_record
    get_my_grade_record = get_student_grade_record
    get_my_grades = get_student_grade_record
    get_grade_record_by_student_user = get_student_grade_record
    get_student_grade_records = get_student_grade_record
    consult_student_grade_record = get_student_grade_record
    list_student_grade_record = get_student_grade_record

    get_gradable_students = get_students_for_grade_registration
    get_students_by_course_for_grading = get_students_for_grade_registration
    list_students_for_grade_registration = get_students_for_grade_registration
    consult_students_for_grade_registration = get_students_for_grade_registration

    get_grade_record_by_course = get_grade_record_by_course_for_user
    get_grade_records_by_course = get_grade_record_by_course_for_user
    get_grade_record_for_user = get_grade_record_by_course_for_user
    get_grade_records_for_user = get_grade_record_by_course_for_user
    consult_grade_record_by_course = get_grade_record_by_course_for_user
    consult_grade_records_by_course = get_grade_record_by_course_for_user
    list_grade_record_by_course = get_grade_record_by_course_for_user
    list_grade_records_by_course = get_grade_record_by_course_for_user

    update_grade = update_grade_for_student
    modify_grade_for_student = update_grade_for_student
    edit_grade_for_student = update_grade_for_student
    correct_grade_for_student = update_grade_for_student
    update_student_grade = update_grade_for_student
    save_grade_changes = update_grade_for_student

    register_grade = register_grade_for_student
    save_grade_for_student = register_grade_for_student
    create_grade_for_student = register_grade_for_student
    assign_grade_to_student = register_grade_for_student
    record_grade_for_student = register_grade_for_student
