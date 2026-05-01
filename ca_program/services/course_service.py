"""
Servicio de cursos.

Coordina la validación de datos de entrada y la interacción con CourseModel para
registrar, consultar, modificar y eliminar cursos. No contiene SQL ni detalles
de persistencia; esos detalles permanecen en la capa models.
"""

from datetime import date
from typing import Any

from ca_program.models.course_model import CourseModel
from ca_program.services import service_utils as utils


class CourseService:
    """Servicio de aplicación para la gestión administrativa de cursos."""

    MIN_NAME_LENGTH = 3
    MIN_DESCRIPTION_LENGTH = 5
    MIN_TEXT_LENGTH = 3

    @staticmethod
    def register_course(data: dict | None = None, **kwargs) -> dict:
        """Registra un curso después de validar datos y profesor asignado."""
        payload = utils.normalize_payload(data, kwargs)

        try:
            clean_data = CourseService._validate_registration_payload(payload)

            if not CourseModel.professor_exists(clean_data["id_professor"]):
                return utils.error_response("El profesor asignado no existe.")

            course = CourseModel.create_course(**clean_data)
            course_data = utils.course_to_dict(course)

            return utils.success_response(
                "Curso registrado correctamente.",
                course=course,
                entity=course,
                data=course_data,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al registrar el curso.",
            )

    @staticmethod
    def update_course(data: dict | None = None, **kwargs) -> dict:
        """
        Modifica un curso existente.

        El código del curso actúa como identificador estable del registro. La
        operación solo actualiza los datos académicos y el profesor asignado.
        """
        payload = utils.normalize_payload(data, kwargs)

        try:
            clean_data = CourseService._validate_update_payload(payload)
            code_course = clean_data.pop("code_course")

            if not CourseModel.course_exists(code_course):
                return utils.error_response("El curso que intenta modificar no existe.")

            if not CourseModel.professor_exists(clean_data["id_professor"]):
                return utils.error_response("El profesor asignado no existe.")

            course = CourseModel.update_course(code_course=code_course, **clean_data)
            course_data = utils.course_to_dict(course)

            return utils.success_response(
                "Curso modificado correctamente.",
                course=course,
                entity=course,
                data=course_data,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al modificar el curso.",
            )

    @staticmethod
    def delete_course(
        code_course: int | str | dict | None = None,
        data: dict | None = None,
        **kwargs,
    ) -> dict:
        """
        Elimina permanentemente un curso.

        Acepta el código como argumento directo o dentro de un diccionario. La
        eliminación en cascada de datos dependientes queda delegada al modelo.
        """
        if isinstance(code_course, dict) and data is None:
            data = code_course
            code_course = None

        payload = utils.normalize_payload(data, kwargs)
        if code_course not in (None, ""):
            payload["code_course"] = code_course

        try:
            clean_code_course = CourseService._validate_delete_payload(payload)

            if not CourseModel.course_exists(clean_code_course):
                return utils.error_response("El curso que intenta eliminar no existe.")

            course = CourseModel.delete_course(clean_code_course)
            course_data = utils.course_to_dict(course)

            return utils.success_response(
                "Curso eliminado correctamente.",
                course=course,
                entity=course,
                data=course_data,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al eliminar el curso.",
            )

    @staticmethod
    def get_courses() -> dict:
        """Consulta todos los cursos registrados."""
        try:
            courses = CourseModel.get_all_courses()
            course_records = [utils.course_to_dict(course) for course in courses]

            return utils.success_response(
                "Cursos consultados correctamente.",
                courses=course_records,
                entities=courses,
                data=course_records,
            )

        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los cursos.",
                courses=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def get_course_by_code(code_course: int | str) -> dict:
        """Consulta un curso por su código."""
        try:
            clean_code_course = CourseService._validate_code_course(code_course)
            course = CourseModel.get_course_by_code(clean_code_course)

            if not course:
                return utils.error_response("Curso no encontrado.")

            course_data = utils.course_to_dict(course)
            return utils.success_response(
                "Curso encontrado.",
                course=course_data,
                entity=course,
                data=course_data,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el curso.",
            )

    @staticmethod
    def get_students_by_course(code_course: int | str) -> dict:
        """Consulta los estudiantes matriculados en un curso."""
        try:
            clean_code_course = CourseService._validate_code_course(code_course)

            if not CourseModel.get_course_by_code(clean_code_course):
                return utils.error_response(
                    "Curso no encontrado.",
                    students=[],
                    data=[],
                )

            students = CourseModel.get_students_by_course(clean_code_course)
            student_records = [utils.student_to_dict(student) for student in students]

            return utils.success_response(
                "Estudiantes del curso consultados correctamente.",
                students=student_records,
                entities=students,
                data=student_records,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), students=[], data=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los estudiantes del curso.",
                students=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def search_courses_by_name(name: str) -> dict:
        """Filtra cursos por nombre usando los datos consultados desde el modelo."""
        try:
            clean_name = str(name or "").strip().lower()
            if not clean_name:
                return CourseService.get_courses()

            result = CourseService.get_courses()
            if not result.get("success"):
                return result

            courses = result.get("courses", [])
            filtered_courses = [
                course
                for course in courses
                if clean_name in str(course.get("name", "")).lower()
            ]

            return utils.success_response(
                "Cursos filtrados correctamente.",
                courses=filtered_courses,
                data=filtered_courses,
            )

        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al buscar cursos.",
                courses=[],
                data=[],
            )

    @staticmethod
    def _validate_registration_payload(payload: dict) -> dict:
        """Valida y normaliza el payload de creación de curso."""
        name = utils.read_first(payload, "name", "course_name")
        description = utils.read_first(payload, "description")
        price = utils.read_first(payload, "price")
        duration_days = utils.read_first(payload, "duration_days", "duration")
        intensity_hours = utils.read_first(payload, "intensity_hours", "intensity")
        schedule = utils.read_first(payload, "schedule")
        location = utils.read_first(payload, "location")
        start_date = utils.read_first(payload, "start_date")
        end_date = utils.read_first(payload, "end_date")
        id_professor = utils.read_first(payload, "id_professor", "professor_id")

        utils.validate_required_fields(
            {
                "nombre": name,
                "descripción": description,
                "precio": price,
                "duración en días": duration_days,
                "intensidad horaria": intensity_hours,
                "horario": schedule,
                "ubicación": location,
                "fecha de inicio": start_date,
                "fecha de finalización": end_date,
                "profesor asignado": id_professor,
            }
        )

        clean_data = {
            "name": utils.clean_text(name, "El nombre del curso", CourseService.MIN_NAME_LENGTH),
            "description": utils.clean_text(description, "La descripción del curso", CourseService.MIN_DESCRIPTION_LENGTH),
            "price": utils.parse_float(price, "El precio debe ser un número válido."),
            "duration_days": utils.parse_int(duration_days, "La duración en días debe ser un número entero válido."),
            "intensity_hours": utils.parse_int(intensity_hours, "La intensidad horaria debe ser un número entero válido."),
            "schedule": utils.clean_text(schedule, "El horario del curso", CourseService.MIN_TEXT_LENGTH),
            "location": utils.clean_text(location, "La ubicación del curso", CourseService.MIN_TEXT_LENGTH),
            "start_date": utils.parse_date(start_date, "La fecha de inicio debe tener formato YYYY-MM-DD."),
            "end_date": utils.parse_date(end_date, "La fecha de finalización debe tener formato YYYY-MM-DD."),
            "id_professor": utils.clean_text(id_professor, "La identificación del profesor asignado", CourseService.MIN_TEXT_LENGTH),
        }

        CourseService._validate_course_business_ranges(clean_data)
        return clean_data

    @staticmethod
    def _validate_update_payload(payload: dict) -> dict:
        """Valida payload de modificación y conserva el código del curso."""
        code_course = utils.read_first(
            payload,
            "code_course",
            "current_code_course",
            "selected_code_course",
            "course_code",
            "current_course_code",
            "selected_course_code",
        )
        clean_code_course = CourseService._validate_code_course(code_course)
        clean_data = CourseService._validate_registration_payload(payload)
        clean_data["code_course"] = clean_code_course
        return clean_data

    @staticmethod
    def _validate_delete_payload(payload: dict) -> str:
        """Valida el código requerido para eliminación."""
        code_course = utils.read_first(
            payload,
            "code_course",
            "current_code_course",
            "selected_code_course",
            "course_code",
            "current_course_code",
            "selected_course_code",
        )
        return CourseService._validate_code_course(code_course)

    @staticmethod
    def _validate_code_course(code_course: int | str | None) -> str:
        """Normaliza y valida el código de curso."""
        if code_course in (None, ""):
            raise ValueError("El código del curso es obligatorio.")

        clean_code_course = str(code_course).strip()
        if not clean_code_course:
            raise ValueError("El código del curso es obligatorio.")

        return clean_code_course

    @staticmethod
    def _validate_course_business_ranges(clean_data: dict[str, Any]) -> None:
        """Valida rangos simples propios de los datos del curso."""
        if clean_data["price"] < 0:
            raise ValueError("El precio del curso no puede ser negativo.")

        if clean_data["duration_days"] <= 0:
            raise ValueError("La duración del curso debe ser mayor que cero.")

        if clean_data["intensity_hours"] <= 0:
            raise ValueError("La intensidad horaria debe ser mayor que cero.")

        start_date: date = clean_data["start_date"]
        end_date: date = clean_data["end_date"]
        if end_date < start_date:
            raise ValueError("La fecha de finalización no puede ser anterior a la fecha de inicio.")

    _normalize_payload = staticmethod(utils.normalize_payload)
    _read_first = staticmethod(utils.read_first)
    _parse_float = staticmethod(utils.parse_float)
    _parse_int = staticmethod(utils.parse_int)
    _parse_date = staticmethod(utils.parse_date)
    _course_to_dict = staticmethod(utils.course_to_dict)
    _student_to_dict = staticmethod(utils.student_to_dict)

    create_course = register_course
    add_course = register_course
    save_course = register_course
    register = register_course

    modify_course = update_course
    edit_course = update_course
    update = update_course
    save_course_changes = update_course

    remove_course = delete_course
    delete_by_code = delete_course
    delete_by_id = delete_course
    delete = delete_course
    destroy_course = delete_course

    list_courses = get_courses
    get_all_courses = get_courses
    consult_courses = get_courses
    get_all = get_courses
