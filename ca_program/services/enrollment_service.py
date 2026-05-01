"""
Servicio de matrículas.

Coordina el flujo de inscripción de estudiantes a cursos, generación de recibos
pendientes y confirmación mediante pago simulado. Mantiene la transacción en el
servicio porque cada flujo combina varios modelos.
"""

from datetime import date, timedelta

from ca_program.entities.fixed_values import PaymentMethod
from ca_program.models.course_model import CourseModel
from ca_program.models.enrollment_model import EnrollmentModel
from ca_program.models.payment_model import PaymentModel
from ca_program.models.receipt_model import ReceiptModel
from ca_program.services import service_utils as utils
from database.connection import get_connection


class EnrollmentService:
    """Servicio para consultar, solicitar y confirmar matrículas de estudiantes."""

    PAYMENT_LIMIT_DAYS = 10

    @staticmethod
    def request_course_enrollment(id_user, code_course) -> dict:
        """
        Solicita inscripción a un curso y genera recibo pendiente.

        La matrícula solo se considera confirmada cuando el recibo queda pagado.
        Si existe un recibo pendiente vencido, se elimina antes de permitir un
        nuevo intento de inscripción.
        """
        connection = None
        cursor = None

        try:
            clean_id_user = utils.validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )
            clean_code_course = utils.validate_required_id(
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

        except ValueError as exc:
            EnrollmentService._rollback(connection)
            return EnrollmentService._response(success=False, message=str(exc))
        except Exception as exc:
            EnrollmentService._rollback(connection)
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al solicitar la inscripción al curso.",
                **EnrollmentService._response_payload_defaults(),
            )
        finally:
            EnrollmentService._close_resources(cursor, connection)

    @staticmethod
    def pay_enrollment_receipt(id_user, code_course, payment_method) -> dict:
        """
        Registra pago simulado de recibo pendiente y confirma la matrícula.

        El cambio de recibo a pagado y la creación del pago se confirman en una
        sola transacción para evitar inconsistencias.
        """
        connection = None
        cursor = None

        try:
            clean_id_user = utils.validate_required_id(
                id_user,
                "El identificador del usuario estudiante es obligatorio.",
            )
            clean_code_course = utils.validate_required_id(
                code_course,
                "El código del curso es obligatorio.",
            )
            clean_payment_method = EnrollmentService._normalize_payment_method(payment_method)

            connection = get_connection()
            cursor = connection.cursor()

            student = EnrollmentModel.get_student_by_user_id_with_cursor(cursor=cursor, id_user=clean_id_user)
            if student is None:
                connection.rollback()
                return EnrollmentService._response(
                    success=False,
                    message="El usuario autenticado no tiene perfil de estudiante.",
                    status=EnrollmentModel.STATUS_NOT_ENROLLED,
                )

            course = CourseModel._get_course_by_code_with_cursor(cursor=cursor, code_course=clean_code_course)
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
                EnrollmentService._delete_expired_pending_enrollment(cursor=cursor, receipt=pending_receipt)
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

            if PaymentModel.payment_exists_for_receipt(cursor=cursor, id_receipt=pending_receipt.id_receipt):
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
            return EnrollmentService._response(
                success=True,
                message=EnrollmentService._build_success_notification(course=course, payment=payment),
                status=EnrollmentModel.STATUS_ENROLLED,
                receipt=paid_receipt,
                payment=payment,
                course=course,
            )

        except ValueError as exc:
            EnrollmentService._rollback(connection)
            return EnrollmentService._response(success=False, message=str(exc))
        except Exception as exc:
            EnrollmentService._rollback(connection)
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al registrar el pago del recibo.",
                **EnrollmentService._response_payload_defaults(),
            )
        finally:
            EnrollmentService._close_resources(cursor, connection)

    @staticmethod
    def get_course_enrollment_status(id_user, code_course) -> dict:
        """Consulta el estado de inscripción frente a un curso."""
        connection = None
        cursor = None

        try:
            clean_id_user = utils.validate_required_id(id_user, "El identificador del usuario estudiante es obligatorio.")
            clean_code_course = utils.validate_required_id(code_course, "El código del curso es obligatorio.")

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
                EnrollmentService._delete_expired_pending_enrollment(cursor=cursor, receipt=receipt)
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

        except ValueError as exc:
            EnrollmentService._rollback(connection)
            return EnrollmentService._response(success=False, message=str(exc))
        except Exception as exc:
            EnrollmentService._rollback(connection)
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el estado de inscripción.",
                **EnrollmentService._response_payload_defaults(),
            )
        finally:
            EnrollmentService._close_resources(cursor, connection)

    @staticmethod
    def get_enrollments_by_student_user_id(id_user) -> dict:
        """Consulta matrículas confirmadas asociadas al usuario estudiante."""
        try:
            clean_id_user = utils.validate_required_id(id_user, "El identificador del usuario estudiante es obligatorio.")

            if not EnrollmentModel.student_user_exists(clean_id_user):
                return utils.error_response(
                    "El usuario autenticado no tiene perfil de estudiante.",
                    enrollments=[],
                    entities=[],
                    data=[],
                )

            enrollments = EnrollmentModel.get_enrollments_by_student_user_id(clean_id_user)
            enrollment_records = [utils.enrollment_to_dict(enrollment) for enrollment in enrollments]

            return utils.success_response(
                "Cursos inscritos consultados correctamente.",
                enrollments=enrollment_records,
                entities=enrollments,
                data=enrollment_records,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), enrollments=[], entities=[], data=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar las matrículas del estudiante.",
                enrollments=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def get_enrollments_by_student_id(id_student: str) -> dict:
        """Consulta matrículas confirmadas usando identificación de estudiante."""
        try:
            clean_id_student = utils.validate_required_id(id_student, "La identificación del estudiante es obligatoria.")
            enrollments = EnrollmentModel.get_enrollments_by_student_id(clean_id_student)
            enrollment_records = [utils.enrollment_to_dict(enrollment) for enrollment in enrollments]

            return utils.success_response(
                "Cursos inscritos consultados correctamente.",
                enrollments=enrollment_records,
                entities=enrollments,
                data=enrollment_records,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), enrollments=[], entities=[], data=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar las matrículas del estudiante.",
                enrollments=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def get_enrolled_courses_by_student_user_id(id_user) -> dict:
        """Retorna cursos inscritos y confirmados por pago del usuario estudiante."""
        try:
            clean_id_user = utils.validate_required_id(id_user, "El identificador del usuario estudiante es obligatorio.")

            if not EnrollmentModel.student_user_exists(clean_id_user):
                return utils.error_response(
                    "El usuario autenticado no tiene perfil de estudiante.",
                    courses=[],
                    entities=[],
                    data=[],
                )

            courses = EnrollmentModel.get_enrolled_courses_by_student_user_id(clean_id_user)
            course_records = [utils.course_to_dict(course) for course in courses]

            return utils.success_response(
                "Cursos inscritos consultados correctamente.",
                courses=course_records,
                entities=courses,
                data=course_records,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), courses=[], entities=[], data=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los cursos inscritos.",
                courses=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def get_enrolled_courses_by_student_id(id_student: str) -> dict:
        """Retorna cursos inscritos confirmados por identificación del estudiante."""
        try:
            clean_id_student = utils.validate_required_id(id_student, "La identificación del estudiante es obligatoria.")
            courses = EnrollmentModel.get_enrolled_courses_by_student_id(clean_id_student)
            course_records = [utils.course_to_dict(course) for course in courses]

            return utils.success_response(
                "Cursos inscritos consultados correctamente.",
                courses=course_records,
                entities=courses,
                data=course_records,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), courses=[], entities=[], data=[])
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los cursos inscritos.",
                courses=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def get_student_by_user_id(id_user) -> dict:
        """Obtiene perfil de estudiante asociado a un usuario del sistema."""
        try:
            clean_id_user = utils.validate_required_id(id_user, "El identificador del usuario estudiante es obligatorio.")
            student = EnrollmentModel.get_student_by_user_id(clean_id_user)

            if student is None:
                return utils.error_response(
                    "El usuario autenticado no tiene perfil de estudiante.",
                    student=None,
                    entity=None,
                    data=None,
                )

            student_data = utils.student_to_dict(student)
            return utils.success_response(
                "Perfil de estudiante consultado correctamente.",
                student=student_data,
                entity=student,
                data=student_data,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), student=None, entity=None, data=None)
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el perfil del estudiante.",
                student=None,
                entity=None,
                data=None,
            )

    @staticmethod
    def _delete_expired_pending_enrollment(cursor, receipt) -> None:
        """Elimina recibo pendiente vencido y matrícula asociada."""
        if receipt is None:
            return

        enrollment = getattr(receipt, "enrollment", None)
        id_enrollment = getattr(enrollment, "id_enrollment", None)

        ReceiptModel.delete_receipt_by_id(cursor=cursor, id_receipt=receipt.id_receipt)

        if id_enrollment is not None:
            EnrollmentModel.delete_enrollment_by_id(cursor=cursor, id_enrollment=id_enrollment)

    @staticmethod
    def _normalize_payment_method(payment_method) -> PaymentMethod:
        """Normaliza nombres de método de pago aceptados por la GUI."""
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
        """Construye mensaje de confirmación de pago e inscripción."""
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
        """Construye respuesta uniforme para flujos de matrícula."""
        enrollment_data = utils.enrollment_to_dict(enrollment) if enrollment else None
        receipt_data = utils.receipt_to_dict(receipt) if receipt else None
        payment_data = utils.payment_to_dict(payment) if payment else None
        course_data = utils.course_to_dict(course) if course else None

        return {
            "success": success,
            "message": message,
            "status": status,
            "enrollment": enrollment_data,
            "receipt": receipt_data,
            "payment": payment_data,
            "course": course_data,
            "entities": {
                "enrollment": enrollment,
                "receipt": receipt,
                "payment": payment,
                "course": course,
            },
            "data": {
                "status": status,
                "enrollment": enrollment_data,
                "receipt": receipt_data,
                "payment": payment_data,
                "course": course_data,
            },
        }

    @staticmethod
    def _response_payload_defaults() -> dict:
        """Devuelve estructura vacía compatible con respuestas de matrícula."""
        return {
            "status": None,
            "enrollment": None,
            "receipt": None,
            "payment": None,
            "course": None,
            "entities": {
                "enrollment": None,
                "receipt": None,
                "payment": None,
                "course": None,
            },
            "data": {
                "status": None,
                "enrollment": None,
                "receipt": None,
                "payment": None,
                "course": None,
            },
        }

    @staticmethod
    def _rollback(connection) -> None:
        """Ejecuta rollback si existe una conexión abierta."""
        if connection:
            connection.rollback()

    @staticmethod
    def _close_resources(cursor, connection) -> None:
        """Cierra recursos de base de datos abiertos por el servicio."""
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    _validate_required_id = staticmethod(utils.validate_required_id)
    _extract_id_value = staticmethod(utils.extract_id_value)
    _enrollment_to_dict = staticmethod(utils.enrollment_to_dict)
    _receipt_to_dict = staticmethod(utils.receipt_to_dict)
    _payment_to_dict = staticmethod(utils.payment_to_dict)
    _student_to_dict = staticmethod(utils.student_to_dict)
    _course_to_dict = staticmethod(utils.course_to_dict)

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
