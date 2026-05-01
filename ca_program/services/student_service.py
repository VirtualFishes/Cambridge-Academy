"""
Servicio de estudiantes.

Valida entradas provenientes de la GUI administrativa y coordina operaciones con
StudentModel. Mantiene la capa de vistas libre de reglas de validación y evita
exponer detalles de persistencia.
"""

from ca_program.models.student_model import StudentModel
from ca_program.services import service_utils as utils


class StudentService:
    """Servicio de aplicación para registro, consulta, modificación y eliminación de estudiantes."""

    MIN_ID_LENGTH = 3
    MIN_NAME_LENGTH = 3
    MIN_PASSWORD_LENGTH = 4
    MIN_NATIONALITY_LENGTH = 3

    @staticmethod
    def register_student(data: dict | None = None, **kwargs) -> dict:
        """Registra un estudiante y su usuario asociado después de validar datos."""
        payload = utils.normalize_payload(data, kwargs)

        try:
            clean_data = StudentService._validate_registration_payload(payload)

            if StudentModel.get_student_by_id(clean_data["id_student"]):
                return utils.error_response("Ya existe un estudiante con esa identificación.")

            if StudentModel.email_exists(clean_data["email"]):
                return utils.error_response("Ya existe un usuario registrado con ese correo electrónico.")

            student = StudentModel.create_student(**clean_data)
            return utils.success_response(
                "Estudiante registrado correctamente.",
                student=student,
                student_data=utils.student_to_dict(student),
                data=student,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al registrar el estudiante.",
            )

    @staticmethod
    def update_student(data: dict | None = None, **kwargs) -> dict:
        """
        Modifica la información de un estudiante existente.

        La identificación actual se usa para localizar el registro. La contraseña
        es opcional; cuando no se envía, se conserva la contraseña actual.
        """
        payload = utils.normalize_payload(data, kwargs)

        try:
            clean_data = StudentService._validate_update_payload(payload)

            current_student = StudentModel.get_student_by_id(clean_data["current_id_student"])
            if not current_student:
                return utils.error_response("El estudiante que intenta modificar no existe.")

            id_changed = clean_data["id_student"] != clean_data["current_id_student"]
            if id_changed and StudentModel.get_student_by_id(clean_data["id_student"]):
                return utils.error_response("Ya existe un estudiante con esa identificación.")

            if StudentModel.email_exists_for_other_student(
                clean_data["email"],
                clean_data["current_id_student"],
            ):
                return utils.error_response("Ya existe otro usuario registrado con ese correo electrónico.")

            student = StudentModel.update_student(**clean_data)
            return utils.success_response(
                "Estudiante modificado correctamente.",
                student=student,
                student_data=utils.student_to_dict(student),
                data=student,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al modificar el estudiante.",
            )

    @staticmethod
    def get_students() -> dict:
        """Consulta todos los estudiantes registrados."""
        try:
            students = StudentModel.get_all_students()
            student_records = [utils.student_to_dict(student) for student in students]

            return utils.success_response(
                "Estudiantes consultados correctamente.",
                students=students,
                student_records=student_records,
                data=students,
            )

        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los estudiantes.",
                students=[],
                student_records=[],
                data=[],
            )

    @staticmethod
    def get_student_by_id(id_student: str) -> dict:
        """Consulta un estudiante por identificación."""
        try:
            clean_id_student = StudentService._validate_id_student(id_student)
            student = StudentModel.get_student_by_id(clean_id_student)

            if not student:
                return utils.error_response("Estudiante no encontrado.")

            return utils.success_response(
                "Estudiante encontrado.",
                student=student,
                student_data=utils.student_to_dict(student),
                data=student,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el estudiante.",
            )

    @staticmethod
    def delete_student(data: dict | str | None = None, **kwargs) -> dict:
        """
        Elimina permanentemente un estudiante y sus datos dependientes.

        Puede recibir la identificación directamente o en un diccionario con
        claves equivalentes usadas por diferentes vistas.
        """
        payload = utils.normalize_delete_payload(data, kwargs, id_key="id_student")

        try:
            id_student = StudentService._validate_delete_payload(payload)

            if not StudentModel.get_student_by_id(id_student):
                return utils.error_response("El estudiante que intenta eliminar no existe.")

            deleted_student = StudentModel.delete_student(id_student)
            return utils.success_response(
                "Estudiante eliminado correctamente.",
                student=deleted_student,
                deleted_student=deleted_student,
                student_data=utils.student_to_dict(deleted_student),
                data=deleted_student,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al eliminar el estudiante.",
            )

    @staticmethod
    def _validate_registration_payload(payload: dict) -> dict:
        """Valida los datos requeridos para crear estudiante."""
        id_student = utils.read_first(payload, "id_student", "identification", "document")
        name = utils.read_first(payload, "name", "student_name")
        password = utils.read_first(payload, "password")
        email = utils.read_first(payload, "email")
        birth_date = utils.read_first(payload, "birth_date", "date_of_birth")
        nationality = utils.read_first(payload, "nationality")

        utils.validate_required_fields(
            {
                "identificación": id_student,
                "nombre": name,
                "contraseña": password,
                "correo electrónico": email,
                "fecha de nacimiento": birth_date,
                "nacionalidad": nationality,
            }
        )

        return {
            "id_student": StudentService._validate_id_student(id_student),
            "name": utils.validate_person_name(
                name,
                "El nombre del estudiante",
                StudentService.MIN_NAME_LENGTH,
            ),
            "password": utils.validate_password_required(
                password,
                "La contraseña inicial",
                StudentService.MIN_PASSWORD_LENGTH,
            ),
            "email": utils.validate_email(email),
            "birth_date": utils.parse_date(
                birth_date,
                "La fecha de nacimiento debe tener formato YYYY-MM-DD.",
                allow_future=False,
                future_error_message="La fecha de nacimiento no puede ser posterior a la fecha actual.",
            ),
            "nationality": utils.validate_alpha_text(
                nationality,
                "La nacionalidad",
                StudentService.MIN_NATIONALITY_LENGTH,
            ),
        }

    @staticmethod
    def _validate_update_payload(payload: dict) -> dict:
        """Valida datos de actualización y contraseña opcional."""
        current_id_student = utils.read_first(
            payload,
            "current_id_student",
            "original_id_student",
            "old_id_student",
            "selected_id_student",
        )
        id_student = (
            utils.read_first(payload, "id_student", "identification", "document")
            or current_id_student
        )
        name = utils.read_first(payload, "name", "student_name")
        password = payload.get("password")
        email = utils.read_first(payload, "email")
        birth_date = utils.read_first(payload, "birth_date", "date_of_birth")
        nationality = utils.read_first(payload, "nationality")

        utils.validate_required_fields(
            {
                "identificación actual": current_id_student,
                "identificación": id_student,
                "nombre": name,
                "correo electrónico": email,
                "fecha de nacimiento": birth_date,
                "nacionalidad": nationality,
            }
        )

        return {
            "current_id_student": StudentService._validate_id_student(
                current_id_student,
                label="La identificación actual del estudiante",
            ),
            "id_student": StudentService._validate_id_student(id_student),
            "name": utils.validate_person_name(
                name,
                "El nombre del estudiante",
                StudentService.MIN_NAME_LENGTH,
            ),
            "password": utils.clean_optional_password(
                password,
                StudentService.MIN_PASSWORD_LENGTH,
            ),
            "email": utils.validate_email(email),
            "birth_date": utils.parse_date(
                birth_date,
                "La fecha de nacimiento debe tener formato YYYY-MM-DD.",
                allow_future=False,
                future_error_message="La fecha de nacimiento no puede ser posterior a la fecha actual.",
            ),
            "nationality": utils.validate_alpha_text(
                nationality,
                "La nacionalidad",
                StudentService.MIN_NATIONALITY_LENGTH,
            ),
        }

    @staticmethod
    def _validate_delete_payload(payload: dict) -> str:
        """Valida el identificador requerido para eliminar."""
        id_student = utils.read_first(
            payload,
            "id_student",
            "current_id_student",
            "selected_id_student",
            "identification",
            "document",
        )
        return StudentService._validate_id_student(id_student)

    @staticmethod
    def _validate_id_student(
        id_student,
        label: str = "La identificación del estudiante",
    ) -> str:
        """Normaliza y valida que la identificación del estudiante sea numérica."""
        return utils.validate_numeric_id(
            id_student,
            field_label=label,
            min_length=StudentService.MIN_ID_LENGTH,
        )

    _normalize_payload = staticmethod(utils.normalize_payload)
    _read_first = staticmethod(utils.read_first)
    _parse_date = staticmethod(utils.parse_date)

    create_student = register_student
    add_student = register_student
    save_student = register_student
    register = register_student

    modify_student = update_student
    edit_student = update_student
    update = update_student
    save_student_changes = update_student

    remove_student = delete_student
    delete_by_id = delete_student
    delete = delete_student
    destroy_student = delete_student

    list_students = get_students
    get_all_students = get_students
    consult_students = get_students
    get_all = get_students
