from datetime import date, timedelta

from ca_program.entities.fixed_values import PaymentMethod
from ca_program.models.course_model import CourseModel
from ca_program.models.enrollment_model import EnrollmentModel
from ca_program.models.payment_model import PaymentModel
from ca_program.models.receipt_model import ReceiptModel
from database.connection import get_connection


class EnrollmentService:
    """Servicio para consultar, solicitar y confirmar matrículas de estudiantes."""

    PAYMENT_LIMIT_DAYS = 10

    @staticmethod
    def request_course_enrollment(id_user, code_course) -> dict:
        """
        Solicita la inscripción de un estudiante a un curso.

        En HU-21, esta acción no confirma todavía la inscripción. El flujo crea
        una matrícula pendiente y un recibo pendiente. La inscripción solo queda
        confirmada cuando el estudiante paga el recibo.
        """
        connection = None
        cursor = None

        try:
            clean_id_user = EnrollmentService._validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )
            clean_code_course = EnrollmentService._validate_required_id(
                code_course,
                "El código del curso es obligatorio.",
            )

            connection = get_connection()
            cursor = connection.cursor()

            student = EnrollmentModel.get_student_by_user_id_with_cursor(
                cursor=cursor,
                id_user=clean_id_user,
            )
            if student is None:
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="El usuario autenticado no tiene perfil de estudiante.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                )

            course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
            )
            if course is None:
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="El curso seleccionado no existe.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                )

            paid_receipt = ReceiptModel.get_paid_receipt_by_student_and_course(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
            )
            if paid_receipt is not None:
                connection.commit()
                return EnrollmentService._response(
                    success=False,
                    message="Ya estás inscrito en este curso.",
                    status=EnrollmentModel.STATUS_ENROLLED,
                    receipt=paid_receipt,
                    course=course,
                )

            pending_receipt = ReceiptModel.get_pending_receipt_by_student_and_course(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
            )
            if pending_receipt is not None:
                if ReceiptModel.is_receipt_expired(pending_receipt):
                    EnrollmentService._delete_expired_pending_enrollment(
                        cursor=cursor,
                        receipt=pending_receipt,
                    )
                else:
                    connection.commit()
                    return EnrollmentService._response(
                        success=True,
                        message="Ya tienes un recibo pendiente para este curso.",
                        status=EnrollmentModel.STATUS_PENDING_PAYMENT,
                        receipt=pending_receipt,
                        course=course,
                    )

            enrollment = EnrollmentModel.create_enrollment(
                cursor=cursor,
                id_student=student.id_student,
                code_course=clean_code_course,
            )

            issue_date = date.today()
            due_date = issue_date + timedelta(days=EnrollmentService.PAYMENT_LIMIT_DAYS)

            receipt = ReceiptModel.create_pending_receipt(
                cursor=cursor,
                id_enrollment=enrollment.id_enrollment,
                amount=course.price,
                issue_date=issue_date,
                due_date=due_date,
            )

            connection.commit()
            return EnrollmentService._response(
                success=True,
                message=(
                    "Se generó un recibo pendiente. "
                    "Para completar la inscripción debes registrar el pago."
                ),
                status=EnrollmentModel.STATUS_PENDING_PAYMENT,
                enrollment=enrollment,
                receipt=receipt,
                course=course,
            )

        except ValueError as e:
            if connection:
                connection.rollback()
            return EnrollmentService._response(success=False, message=str(e))

        except Exception as e:
            if connection:
                connection.rollback()
            print(e)
            return EnrollmentService._response(
                success=False,
                message="Ocurrió un error al solicitar la inscripción al curso.",
            )

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def pay_enrollment_receipt(id_user, code_course, payment_method) -> dict:
        """
        Registra el pago simulado de un recibo pendiente.

        Al completarse este proceso, se crea el pago, el recibo pasa a estado
        pagado y la matrícula queda confirmada funcionalmente.
        """
        connection = None
        cursor = None

        try:
            clean_id_user = EnrollmentService._validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )
            clean_code_course = EnrollmentService._validate_required_id(
                code_course,
                "El código del curso es obligatorio.",
            )
            clean_payment_method = EnrollmentService._normalize_payment_method(payment_method)

            connection = get_connection()
            cursor = connection.cursor()

            student = EnrollmentModel.get_student_by_user_id_with_cursor(
                cursor=cursor,
                id_user=clean_id_user,
            )
            if student is None:
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="El usuario autenticado no tiene perfil de estudiante.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                )

            course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
            )
            if course is None:
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="El curso seleccionado no existe.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                )

            paid_receipt = ReceiptModel.get_paid_receipt_by_student_and_course(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
            )
            if paid_receipt is not None:
                connection.commit()
                return EnrollmentService._response(
                    success=False,
                    message="Este curso ya tiene una inscripción confirmada.",
                    status=EnrollmentModel.STATUS_ENROLLED,
                    receipt=paid_receipt,
                    course=course,
                )

            pending_receipt = ReceiptModel.get_pending_receipt_by_student_and_course(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
            )
            if pending_receipt is None:
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="No existe un recibo pendiente para este curso.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                    course=course,
                )

            if ReceiptModel.is_receipt_expired(pending_receipt):
                EnrollmentService._delete_expired_pending_enrollment(
                    cursor=cursor,
                    receipt=pending_receipt,
                )
                connection.commit()
                return EnrollmentService._response(
                    success=False,
                    message=(
                        "El recibo pendiente estaba vencido. "
                        "La inscripción pendiente fue eliminada y puedes intentarlo nuevamente."
                    ),
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                    course=course,
                )

            if PaymentModel.payment_exists_for_receipt(
                cursor=cursor,
                id_receipt=pending_receipt.id_receipt,
            ):
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="Este recibo ya tiene un pago registrado.",
                    status=EnrollmentModel.STATUS_PENDING_PAYMENT,
                    receipt=pending_receipt,
                    course=course,
                )

            payment = PaymentModel.create_payment(
                cursor=cursor,
                id_receipt=pending_receipt.id_receipt,
                payment_method=clean_payment_method,
                payment_date=date.today(),
            )
            paid_receipt = ReceiptModel.mark_receipt_as_paid(
                cursor=cursor,
                id_receipt=pending_receipt.id_receipt,
            )

            if paid_receipt is None:
                raise ValueError("No fue posible actualizar el recibo como pagado.")

            connection.commit()
            notification = EnrollmentService._build_success_notification(
                course=course,
                payment=payment,
            )

            return EnrollmentService._response(
                success=True,
                message=notification,
                status=EnrollmentModel.STATUS_ENROLLED,
                receipt=paid_receipt,
                payment=payment,
                course=course,
            )

        except ValueError as e:
            if connection:
                connection.rollback()
            return EnrollmentService._response(success=False, message=str(e))

        except Exception as e:
            if connection:
                connection.rollback()
            print(e)
            return EnrollmentService._response(
                success=False,
                message="Ocurrió un error al registrar el pago del recibo.",
            )

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def get_course_enrollment_status(id_user, code_course) -> dict:
        """
        Consulta el estado de inscripción del estudiante frente a un curso.

        Si detecta un recibo pendiente vencido, elimina permanentemente el recibo
        y la matrícula asociada, dejando el curso disponible para un nuevo intento.
        """
        connection = None
        cursor = None

        try:
            clean_id_user = EnrollmentService._validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )
            clean_code_course = EnrollmentService._validate_required_id(
                code_course,
                "El código del curso es obligatorio.",
            )

            connection = get_connection()
            cursor = connection.cursor()

            status = EnrollmentModel.get_course_enrollment_status(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
            )
            receipt = ReceiptModel.get_receipt_by_student_and_course(
                cursor=cursor,
                id_user=clean_id_user,
                code_course=clean_code_course,
            )

            if status == EnrollmentModel.STATUS_EXPIRED and receipt is not None:
                EnrollmentService._delete_expired_pending_enrollment(
                    cursor=cursor,
                    receipt=receipt,
                )
                connection.commit()
                return EnrollmentService._response(
                    success=True,
                    message="La inscripción pendiente vencida fue eliminada.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                )

            connection.commit()
            return EnrollmentService._response(
                success=True,
                message="Estado de inscripción consultado correctamente.",
                status=status,
                receipt=receipt,
            )

        except ValueError as e:
            if connection:
                connection.rollback()
            return EnrollmentService._response(success=False, message=str(e))

        except Exception as e:
            if connection:
                connection.rollback()
            print(e)
            return EnrollmentService._response(
                success=False,
                message="Ocurrió un error al consultar el estado de inscripción.",
            )

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def get_enrollments_by_student_user_id(id_user) -> dict:
        """
        Consulta las matrículas confirmadas asociadas al usuario estudiante.

        Desde HU-21, una matrícula solo se considera confirmada si tiene recibo
        pagado. Las matrículas pendientes de pago no aparecen aquí.
        """
        try:
            clean_id_user = EnrollmentService._validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )

            if not EnrollmentModel.student_user_exists(clean_id_user):
                return {
                    "success": False,
                    "message": "El usuario autenticado no tiene perfil de estudiante.",
                    "enrollments": [],
                    "entities": [],
                    "data": [],
                }

            enrollments = EnrollmentModel.get_enrollments_by_student_user_id(clean_id_user)
            enrollment_records = [
                EnrollmentService._enrollment_to_dict(enrollment)
                for enrollment in enrollments
            ]

            return {
                "success": True,
                "message": "Cursos inscritos consultados correctamente.",
                "enrollments": enrollment_records,
                "entities": enrollments,
                "data": enrollment_records,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "enrollments": [],
                "entities": [],
                "data": [],
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar las matrículas del estudiante.",
                "enrollments": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def get_enrollments_by_student_id(id_student: str) -> dict:
        """Consulta las matrículas confirmadas usando la identificación del estudiante."""
        try:
            clean_id_student = EnrollmentService._validate_required_id(
                id_student,
                "La identificación del estudiante es obligatoria.",
            )

            enrollments = EnrollmentModel.get_enrollments_by_student_id(clean_id_student)
            enrollment_records = [
                EnrollmentService._enrollment_to_dict(enrollment)
                for enrollment in enrollments
            ]

            return {
                "success": True,
                "message": "Cursos inscritos consultados correctamente.",
                "enrollments": enrollment_records,
                "entities": enrollments,
                "data": enrollment_records,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "enrollments": [],
                "entities": [],
                "data": [],
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar las matrículas del estudiante.",
                "enrollments": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def get_enrolled_courses_by_student_user_id(id_user) -> dict:
        """
        Retorna los cursos inscritos confirmados por pago del usuario estudiante.
        """
        try:
            clean_id_user = EnrollmentService._validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )

            if not EnrollmentModel.student_user_exists(clean_id_user):
                return {
                    "success": False,
                    "message": "El usuario autenticado no tiene perfil de estudiante.",
                    "courses": [],
                    "entities": [],
                    "data": [],
                }

            courses = EnrollmentModel.get_enrolled_courses_by_student_user_id(clean_id_user)
            course_records = [EnrollmentService._course_to_dict(course) for course in courses]

            return {
                "success": True,
                "message": "Cursos inscritos consultados correctamente.",
                "courses": course_records,
                "entities": courses,
                "data": course_records,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "courses": [],
                "entities": [],
                "data": [],
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los cursos inscritos.",
                "courses": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def get_enrolled_courses_by_student_id(id_student: str) -> dict:
        """Retorna los cursos inscritos confirmados usando la identificación del estudiante."""
        try:
            clean_id_student = EnrollmentService._validate_required_id(
                id_student,
                "La identificación del estudiante es obligatoria.",
            )

            courses = EnrollmentModel.get_enrolled_courses_by_student_id(clean_id_student)
            course_records = [EnrollmentService._course_to_dict(course) for course in courses]

            return {
                "success": True,
                "message": "Cursos inscritos consultados correctamente.",
                "courses": course_records,
                "entities": courses,
                "data": course_records,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "courses": [],
                "entities": [],
                "data": [],
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los cursos inscritos.",
                "courses": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def get_student_by_user_id(id_user) -> dict:
        """Obtiene el perfil de estudiante asociado a un usuario del sistema."""
        try:
            clean_id_user = EnrollmentService._validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )

            student = EnrollmentModel.get_student_by_user_id(clean_id_user)

            if student is None:
                return {
                    "success": False,
                    "message": "El usuario autenticado no tiene perfil de estudiante.",
                    "student": None,
                    "entity": None,
                    "data": None,
                }

            student_data = EnrollmentService._student_to_dict(student)

            return {
                "success": True,
                "message": "Perfil de estudiante consultado correctamente.",
                "student": student_data,
                "entity": student,
                "data": student_data,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "student": None,
                "entity": None,
                "data": None,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el perfil del estudiante.",
                "student": None,
                "entity": None,
                "data": None,
            }

    @staticmethod
    def _delete_expired_pending_enrollment(cursor, receipt) -> None:
        """
        Elimina permanentemente el recibo pendiente vencido y su matrícula.
        """
        if receipt is None:
            return

        enrollment = getattr(receipt, "enrollment", None)
        id_enrollment = getattr(enrollment, "id_enrollment", None)

        ReceiptModel.delete_receipt_by_id(
            cursor=cursor,
            id_receipt=receipt.id_receipt,
        )

        if id_enrollment is not None:
            EnrollmentModel.delete_enrollment_by_id(
                cursor=cursor,
                id_enrollment=id_enrollment,
            )

    @staticmethod
    def _normalize_payment_method(payment_method) -> PaymentMethod:
        if isinstance(payment_method, PaymentMethod):
            return payment_method

        if payment_method is None:
            raise ValueError("El método de pago es obligatorio.")

        value = str(payment_method).strip()
        if not value:
            raise ValueError("El método de pago es obligatorio.")

        aliases = {
            "efectivo": PaymentMethod.CASH,
            "cash": PaymentMethod.CASH,
            "transferencia": PaymentMethod.BANK,
            "transferencia bancaria": PaymentMethod.BANK,
            "bank": PaymentMethod.BANK,
            "bank_transfer": PaymentMethod.BANK,
            "tarjeta": PaymentMethod.CARD,
            "card": PaymentMethod.CARD,
        }

        normalized = value.lower()
        if normalized in aliases:
            return aliases[normalized]

        try:
            return PaymentMethod(value)
        except ValueError as exc:
            raise ValueError("Método de pago no válido.") from exc

    @staticmethod
    def _build_success_notification(course, payment) -> str:
        course_name = getattr(course, "name", "el curso seleccionado")
        payment_method = getattr(getattr(payment, "payment_method", None), "value", "")

        if payment_method:
            return (
                "Pago registrado correctamente. "
                f"Tu inscripción al curso {course_name} ha sido completada. "
                f"Método de pago: {payment_method}."
            )

        return (
            "Pago registrado correctamente. "
            f"Tu inscripción al curso {course_name} ha sido completada."
        )

    @staticmethod
    def _response(
        success: bool,
        message: str,
        status: str | None = None,
        enrollment=None,
        receipt=None,
        payment=None,
        course=None,
    ) -> dict:
        return {
            "success": success,
            "message": message,
            "status": status,
            "enrollment": EnrollmentService._enrollment_to_dict(enrollment) if enrollment else None,
            "receipt": EnrollmentService._receipt_to_dict(receipt) if receipt else None,
            "payment": EnrollmentService._payment_to_dict(payment) if payment else None,
            "course": EnrollmentService._course_to_dict(course) if course else None,
            "entities": {
                "enrollment": enrollment,
                "receipt": receipt,
                "payment": payment,
                "course": course,
            },
            "data": {
                "status": status,
                "enrollment": EnrollmentService._enrollment_to_dict(enrollment) if enrollment else None,
                "receipt": EnrollmentService._receipt_to_dict(receipt) if receipt else None,
                "payment": EnrollmentService._payment_to_dict(payment) if payment else None,
                "course": EnrollmentService._course_to_dict(course) if course else None,
            },
        }

    @staticmethod
    def _validate_required_id(value, error_message: str) -> str:
        clean_value = EnrollmentService._extract_id_value(value)

        if clean_value is None:
            raise ValueError(error_message)

        clean_value = str(clean_value).strip()

        if not clean_value:
            raise ValueError(error_message)

        return clean_value

    @staticmethod
    def _extract_id_value(value):
        """
        Permite recibir directamente el ID, un User o un diccionario simple.
        Esto facilita la integración con LoginGUI y StudentGUI sin romper capas.
        """
        if isinstance(value, dict):
            return (
                value.get("id_user")
                or value.get("user_id")
                or value.get("id_student")
                or value.get("student_id")
                or value.get("code_course")
                or value.get("id")
            )

        for attribute in ("id_user", "user_id", "id_student", "student_id", "code_course", "id"):
            if hasattr(value, attribute):
                return getattr(value, attribute)

        return value

    @staticmethod
    def _enrollment_to_dict(enrollment) -> dict:
        if enrollment is None:
            return {}

        return {
            "id_enrollment": getattr(enrollment, "id_enrollment", ""),
            "student": EnrollmentService._student_to_dict(getattr(enrollment, "student", None)),
            "course": EnrollmentService._course_to_dict(getattr(enrollment, "course", None)),
        }

    @staticmethod
    def _receipt_to_dict(receipt) -> dict:
        if receipt is None:
            return {}

        status = getattr(receipt, "status", "")
        enrollment = getattr(receipt, "enrollment", None)

        return {
            "id_receipt": getattr(receipt, "id_receipt", ""),
            "issue_date": getattr(receipt, "issue_date", ""),
            "due_date": getattr(receipt, "due_date", ""),
            "amount": getattr(receipt, "amount", 0),
            "status": getattr(status, "value", status),
            "enrollment": EnrollmentService._enrollment_to_dict(enrollment),
        }

    @staticmethod
    def _payment_to_dict(payment) -> dict:
        if payment is None:
            return {}

        payment_method = getattr(payment, "payment_method", "")

        return {
            "id_payment": getattr(payment, "id_payment", ""),
            "payment_date": getattr(payment, "payment_date", ""),
            "payment_method": getattr(payment_method, "value", payment_method),
            "receipt": EnrollmentService._receipt_to_dict(getattr(payment, "receipt", None)),
        }

    @staticmethod
    def _student_to_dict(student) -> dict:
        if student is None:
            return {}

        user = getattr(student, "user", None)

        return {
            "id_student": getattr(student, "id_student", ""),
            "id_user": getattr(user, "id_user", ""),
            "name": getattr(user, "name", ""),
            "email": getattr(user, "email", ""),
            "birth_date": getattr(user, "birth_date", ""),
            "nationality": getattr(user, "nationality", ""),
        }

    @staticmethod
    def _course_to_dict(course) -> dict:
        if course is None:
            return {}

        professor = getattr(course, "professor", None)
        professor_user = getattr(professor, "user", None)

        professor_data = {
            "id_professor": getattr(professor, "id_professor", ""),
            "name": getattr(professor_user, "name", ""),
            "email": getattr(professor_user, "email", ""),
            "professional_title": getattr(professor, "professional_title", ""),
        }

        return {
            "code_course": getattr(course, "code_course", ""),
            "name": getattr(course, "name", ""),
            "description": getattr(course, "description", ""),
            "price": getattr(course, "price", 0),
            "duration_days": getattr(course, "duration_days", 0),
            "intensity_hours": getattr(course, "intensity_hours", 0),
            "schedule": getattr(course, "schedule", ""),
            "location": getattr(course, "location", ""),
            "start_date": getattr(course, "start_date", ""),
            "end_date": getattr(course, "end_date", ""),
            "id_professor": professor_data["id_professor"],
            "professor": professor_data,
            "students": getattr(course, "enrolled_students", 0),
            "enrolled_students": getattr(course, "enrolled_students", 0),
        }

    list_enrollments_by_student_user_id = get_enrollments_by_student_user_id
    consult_enrollments_by_student_user_id = get_enrollments_by_student_user_id
    list_enrollments_by_student_id = get_enrollments_by_student_id
    consult_enrollments_by_student_id = get_enrollments_by_student_id

    list_enrolled_courses_by_student_user_id = get_enrolled_courses_by_student_user_id
    consult_enrolled_courses_by_student_user_id = get_enrolled_courses_by_student_user_id
    get_student_courses_by_user_id = get_enrolled_courses_by_student_user_id
    get_my_courses = get_enrolled_courses_by_student_user_id

    list_enrolled_courses_by_student_id = get_enrolled_courses_by_student_id
    consult_enrolled_courses_by_student_id = get_enrolled_courses_by_student_id
    get_student_courses_by_student_id = get_enrolled_courses_by_student_id

    enroll_student_in_course = request_course_enrollment
    request_enrollment = request_course_enrollment
    pay_receipt = pay_enrollment_receipt
    confirm_enrollment_payment = pay_enrollment_receipt
    consult_course_enrollment_status = get_course_enrollment_status
