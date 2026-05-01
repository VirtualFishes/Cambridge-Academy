"""
Servicio de profesores.

Valida solicitudes administrativas y de consulta docente, coordina operaciones
con ProfessorModel y CourseModel, y devuelve respuestas homogéneas para la GUI.
"""

from ca_program.models.course_model import CourseModel
from ca_program.models.professor_model import ProfessorModel
from ca_program.services import service_utils as utils


class ProfessorService:
    """Servicio de aplicación para gestión administrativa y consultas de profesor."""

    MIN_ID_LENGTH = 3
    MIN_NAME_LENGTH = 3
    MIN_PASSWORD_LENGTH = 4
    MIN_TEXT_LENGTH = 3

    @staticmethod
    def register_professor(data: dict | None = None, **kwargs) -> dict:
        """Registra un profesor y su usuario asociado."""
        payload = utils.normalize_payload(data, kwargs)

        try:
            clean_data = ProfessorService._validate_registration_payload(payload)

            if ProfessorModel.get_professor_by_id(clean_data["id_professor"]):
                return utils.error_response("Ya existe un profesor con esa identificación.")

            if ProfessorModel.email_exists(clean_data["email"]):
                return utils.error_response("Ya existe un usuario registrado con ese correo electrónico.")

            professor = ProfessorModel.create_professor(**clean_data)
            return utils.success_response(
                "Profesor registrado correctamente.",
                professor=professor,
                professor_data=utils.professor_to_dict(professor),
                data=professor,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al registrar el profesor.",
            )

    @staticmethod
    def update_professor(data: dict | None = None, **kwargs) -> dict:
        """
        Modifica la información de un profesor existente.

        La contraseña es opcional. Si no se envía, se conserva la contraseña
        actual del usuario asociado.
        """
        payload = utils.normalize_payload(data, kwargs)

        try:
            clean_data = ProfessorService._validate_update_payload(payload)

            current_professor = ProfessorModel.get_professor_by_id(clean_data["current_id_professor"])
            if not current_professor:
                return utils.error_response("El profesor que intenta modificar no existe.")

            id_changed = clean_data["id_professor"] != clean_data["current_id_professor"]
            if id_changed and ProfessorModel.get_professor_by_id(clean_data["id_professor"]):
                return utils.error_response("Ya existe un profesor con esa identificación.")

            professor = ProfessorModel.update_professor(**clean_data)
            return utils.success_response(
                "Profesor modificado correctamente.",
                professor=professor,
                professor_data=utils.professor_to_dict(professor),
                data=professor,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al modificar el profesor.",
            )

    @staticmethod
    def delete_professor(data: dict | str | None = None, **kwargs) -> dict:
        """
        Elimina permanentemente un profesor sin cursos asignados.

        La restricción protege la historia académica: un curso no debe
        desaparecer automáticamente al borrar su profesor.
        """
        payload = utils.normalize_delete_payload(data, kwargs, id_key="id_professor")

        try:
            id_professor = ProfessorService._validate_delete_payload(payload)

            professor = ProfessorModel.get_professor_by_id(id_professor)
            if not professor:
                return utils.error_response("El profesor que intenta eliminar no existe.")

            if ProfessorModel.has_assigned_courses(id_professor):
                return utils.error_response(
                    "No se puede eliminar el profesor porque tiene cursos asignados. "
                    "Primero debe reasignar o eliminar esos cursos."
                )

            deleted_professor = ProfessorModel.delete_professor(id_professor)
            return utils.success_response(
                "Profesor eliminado correctamente.",
                professor=deleted_professor,
                professor_data=utils.professor_to_dict(deleted_professor),
                data=deleted_professor,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al eliminar el profesor.",
            )

    @staticmethod
    def get_professors() -> dict:
        """Consulta todos los profesores registrados."""
        try:
            professors = ProfessorModel.get_all_professors()
            professor_records = [utils.professor_to_dict(professor) for professor in professors]
            return utils.success_response(
                "Profesores consultados correctamente.",
                professors=professors,
                professor_records=professor_records,
                data=professors,
            )

        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los profesores.",
                professors=[],
                professor_records=[],
                data=[],
            )

    @staticmethod
    def get_professor_by_id(id_professor: str) -> dict:
        """Consulta un profesor por identificación."""
        try:
            clean_id_professor = ProfessorService._validate_id_professor(id_professor)
            professor = ProfessorModel.get_professor_by_id(clean_id_professor)

            if not professor:
                return utils.error_response("Profesor no encontrado.")

            return utils.success_response(
                "Profesor encontrado.",
                professor=professor,
                professor_data=utils.professor_to_dict(professor),
                data=professor,
            )

        except ValueError as exc:
            return utils.error_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el profesor.",
            )

    @staticmethod
    def get_professor_by_user_id(id_user: int | str) -> dict:
        """Consulta el perfil docente asociado al usuario autenticado."""
        try:
            clean_id_user = utils.extract_user_id(id_user=id_user)
            professor = ProfessorModel.get_professor_by_user_id(clean_id_user)

            if not professor:
                return utils.error_response(
                    "No existe un perfil de profesor asociado a este usuario.",
                    professor=None,
                    data=None,
                )

            return utils.success_response(
                "Profesor encontrado.",
                professor=professor,
                professor_data=utils.professor_to_dict(professor),
                data=professor,
            )

        except ValueError as exc:
            return utils.error_response(str(exc), professor=None, data=None)
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el perfil del profesor.",
                professor=None,
                data=None,
            )

    @staticmethod
    def get_assigned_courses_by_user(user=None, id_user: int | str | None = None) -> dict:
        """
        Consulta los cursos asignados al profesor autenticado.

        Soporta HU-24 y evita que la GUI consulte modelos directamente.
        """
        try:
            if not ProfessorService._user_has_professor_role(user):
                return ProfessorService._empty_assigned_courses_response(
                    "El usuario autenticado no tiene permisos de profesor."
                )

            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)
            professor = ProfessorModel.get_professor_by_user_id(clean_id_user)

            if not professor:
                return ProfessorService._empty_assigned_courses_response(
                    "No existe un perfil de profesor asociado a este usuario."
                )

            courses = CourseModel.get_courses_by_professor_id(professor.id_professor)
            course_records = [utils.course_to_dict(course) for course in courses]

            return utils.success_response(
                "Cursos asignados consultados correctamente.",
                professor=professor,
                professor_data=utils.professor_to_dict(professor),
                courses=course_records,
                entities=courses,
                data=course_records,
            )

        except ValueError as exc:
            return ProfessorService._empty_assigned_courses_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar los cursos asignados.",
                professor=None,
                professor_data=None,
                courses=[],
                entities=[],
                data=[],
            )

    @staticmethod
    def get_assigned_course_detail_by_user(
        user=None,
        id_user: int | str | None = None,
        code_course: str | None = None,
    ) -> dict:
        """
        Consulta el detalle de un curso asignado al profesor autenticado.

        Soporta HU-25 validando profesor y código de curso en la misma operación.
        """
        try:
            if not ProfessorService._user_has_professor_role(user):
                return ProfessorService._empty_course_detail_response(
                    "El usuario autenticado no tiene permisos de profesor."
                )

            clean_code_course = utils.clean_text(
                code_course,
                "El código del curso",
                min_length=1,
            )
            clean_id_user = utils.extract_user_id(user=user, id_user=id_user)
            professor = ProfessorModel.get_professor_by_user_id(clean_id_user)

            if not professor:
                return ProfessorService._empty_course_detail_response(
                    "No existe un perfil de profesor asociado a este usuario."
                )

            course = CourseModel.get_course_by_code_and_professor_id(
                code_course=clean_code_course,
                id_professor=professor.id_professor,
            )
            if not course:
                return utils.error_response(
                    "Curso no encontrado o no asignado al profesor autenticado.",
                    professor=professor,
                    professor_data=utils.professor_to_dict(professor),
                    course=None,
                    entity=None,
                    data=None,
                )

            course_record = utils.course_to_dict(course)
            return utils.success_response(
                "Detalle del curso consultado correctamente.",
                professor=professor,
                professor_data=utils.professor_to_dict(professor),
                course=course_record,
                entity=course,
                data=course_record,
            )

        except ValueError as exc:
            return ProfessorService._empty_course_detail_response(str(exc))
        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al consultar el detalle del curso asignado.",
                professor=None,
                professor_data=None,
                course=None,
                entity=None,
                data=None,
            )

    @staticmethod
    def search_professors_by_name(name: str) -> dict:
        """Filtra profesores por nombre."""
        try:
            clean_name = str(name or "").strip().lower()
            if not clean_name:
                return ProfessorService.get_professors()

            result = ProfessorService.get_professors()
            if not result.get("success"):
                return result

            professors = result.get("professors", [])
            filtered_professors = [
                professor
                for professor in professors
                if clean_name in str(getattr(getattr(professor, "user", None), "name", "")).lower()
            ]

            return utils.success_response(
                "Profesores filtrados correctamente.",
                professors=filtered_professors,
                professor_records=[utils.professor_to_dict(professor) for professor in filtered_professors],
                data=filtered_professors,
            )

        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error al buscar profesores.",
                professors=[],
                data=[],
            )

    @staticmethod
    def _validate_registration_payload(payload: dict) -> dict:
        """Valida datos de creación de profesor."""
        id_professor = utils.read_first(payload, "id_professor", "identification", "document")
        name = utils.read_first(payload, "name", "professor_name")
        password = utils.read_first(payload, "password")
        email = utils.read_first(payload, "email")
        birth_date = utils.read_first(payload, "birth_date", "date_of_birth")
        nationality = utils.read_first(payload, "nationality")
        professional_title = utils.read_first(
            payload,
            "professional_title",
            "title",
            "profession",
            "specialty",
        )

        utils.validate_required_fields(
            {
                "identificación": id_professor,
                "nombre": name,
                "contraseña": password,
                "correo electrónico": email,
                "fecha de nacimiento": birth_date,
                "nacionalidad": nationality,
                "título profesional": professional_title,
            }
        )

        return {
            "id_professor": ProfessorService._validate_id_professor(id_professor),
            "name": utils.validate_person_name(
                name,
                "El nombre del profesor",
                ProfessorService.MIN_NAME_LENGTH,
            ),
            "password": utils.validate_password_required(
                password,
                "La contraseña inicial",
                ProfessorService.MIN_PASSWORD_LENGTH,
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
                ProfessorService.MIN_TEXT_LENGTH,
            ),
            "professional_title": utils.validate_alpha_text(
                professional_title,
                "El título profesional",
                ProfessorService.MIN_TEXT_LENGTH,
            ),
        }

    @staticmethod
    def _validate_update_payload(payload: dict) -> dict:
        """Valida payload de actualización de profesor."""
        current_id_professor = utils.read_first(
            payload,
            "current_id_professor",
            "original_id_professor",
            "old_id_professor",
            "selected_id_professor",
        )
        id_professor = (
            utils.read_first(payload, "id_professor", "identification", "document")
            or current_id_professor
        )
        name = utils.read_first(payload, "name", "professor_name")
        password = payload.get("password")
        email = utils.read_first(payload, "email")
        birth_date = utils.read_first(payload, "birth_date", "date_of_birth")
        nationality = utils.read_first(payload, "nationality")
        professional_title = utils.read_first(
            payload,
            "professional_title",
            "title",
            "profession",
            "specialty",
        )

        utils.validate_required_fields(
            {
                "identificación actual": current_id_professor,
                "identificación": id_professor,
                "nombre": name,
                "correo electrónico": email,
                "fecha de nacimiento": birth_date,
                "nacionalidad": nationality,
                "título profesional": professional_title,
            }
        )

        return {
            "current_id_professor": ProfessorService._validate_id_professor(
                current_id_professor,
                label="La identificación actual del profesor",
            ),
            "id_professor": ProfessorService._validate_id_professor(id_professor),
            "name": utils.validate_person_name(
                name,
                "El nombre del profesor",
                ProfessorService.MIN_NAME_LENGTH,
            ),
            "password": utils.clean_optional_password(
                password,
                ProfessorService.MIN_PASSWORD_LENGTH,
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
                ProfessorService.MIN_TEXT_LENGTH,
            ),
            "professional_title": utils.validate_alpha_text(
                professional_title,
                "El título profesional",
                ProfessorService.MIN_TEXT_LENGTH,
            ),
        }

    @staticmethod
    def _validate_delete_payload(payload: dict) -> str:
        """Valida identificación requerida para eliminación."""
        id_professor = utils.read_first(
            payload,
            "id_professor",
            "current_id_professor",
            "selected_id_professor",
            "identification",
            "document",
        )
        return ProfessorService._validate_id_professor(id_professor)

    @staticmethod
    def _validate_id_professor(
        id_professor,
        label: str = "La identificación del profesor",
    ) -> str:
        """Normaliza y valida que la identificación del profesor sea numérica."""
        return utils.validate_numeric_id(
            id_professor,
            field_label=label,
            min_length=ProfessorService.MIN_ID_LENGTH,
        )
        
    @staticmethod
    def _user_has_professor_role(user) -> bool:
        """Valida rol de profesor permitiendo compatibilidad cuando no se envía usuario."""
        return utils.role_matches(user, {"professor"}, allow_missing=True)

    @staticmethod
    def _empty_assigned_courses_response(message: str) -> dict:
        return utils.error_response(
            message,
            professor=None,
            professor_data=None,
            courses=[],
            entities=[],
            data=[],
        )

    @staticmethod
    def _empty_course_detail_response(message: str) -> dict:
        return utils.error_response(
            message,
            professor=None,
            professor_data=None,
            course=None,
            entity=None,
            data=None,
        )

    _normalize_payload = staticmethod(utils.normalize_payload)
    _normalize_delete_payload = staticmethod(utils.normalize_delete_payload)
    _read_first = staticmethod(utils.read_first)
    _parse_date = staticmethod(utils.parse_date)
    _extract_user_id = staticmethod(utils.extract_user_id)
    _professor_to_dict = staticmethod(utils.professor_to_dict)
    _course_to_dict = staticmethod(utils.course_to_dict)

    create_professor = register_professor
    add_professor = register_professor
    save_professor = register_professor
    register = register_professor

    modify_professor = update_professor
    edit_professor = update_professor
    update = update_professor
    save_professor_changes = update_professor

    remove_professor = delete_professor
    delete_by_id = delete_professor
    delete = delete_professor
    destroy_professor = delete_professor

    list_professors = get_professors
    get_all_professors = get_professors
    consult_professors = get_professors
    get_all = get_professors

    find_professors_by_name = search_professors_by_name
    search_by_name = search_professors_by_name

    find_professor_by_user_id = get_professor_by_user_id
    get_by_user_id = get_professor_by_user_id

    get_assigned_course_detail_for_user = get_assigned_course_detail_by_user
    get_course_detail_by_user = get_assigned_course_detail_by_user
    get_my_course_detail = get_assigned_course_detail_by_user
    consult_assigned_course_detail = get_assigned_course_detail_by_user
    get_assigned_course_by_code_for_user = get_assigned_course_detail_by_user

    get_assigned_courses_for_user = get_assigned_courses_by_user
    get_courses_by_user = get_assigned_courses_by_user
    get_my_courses = get_assigned_courses_by_user
    consult_assigned_courses = get_assigned_courses_by_user
    list_assigned_courses = get_assigned_courses_by_user
