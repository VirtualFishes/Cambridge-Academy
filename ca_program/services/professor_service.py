import re
from datetime import date, datetime

from ca_program.models.professor_model import ProfessorModel
from ca_program.models.course_model import CourseModel


class ProfessorService:
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    @staticmethod
    def register_professor(data: dict | None = None, **kwargs) -> dict:
        payload = ProfessorService._normalize_payload(data, kwargs)

        try:
            clean_data = ProfessorService._validate_registration_payload(payload)

            if ProfessorModel.get_professor_by_id(clean_data["id_professor"]):
                return {
                    "success": False,
                    "message": "Ya existe un profesor con esa identificación.",
                }

            if ProfessorModel.email_exists(clean_data["email"]):
                return {
                    "success": False,
                    "message": "Ya existe un usuario registrado con ese correo electrónico.",
                }

            professor = ProfessorModel.create_professor(**clean_data)

            return {
                "success": True,
                "message": "Profesor registrado correctamente.",
                "professor": professor,
                "data": professor,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al registrar el profesor.",
            }

    @staticmethod
    def update_professor(data: dict | None = None, **kwargs) -> dict:
        """
        Modifica la información de un profesor existente.

        La identificación actual debe llegar en current_id_professor. Los datos
        personales se actualizan sobre el usuario asociado al profesor.
        La contraseña es opcional: si llega vacía, se conserva la actual.
        """
        payload = ProfessorService._normalize_payload(data, kwargs)

        try:
            clean_data = ProfessorService._validate_update_payload(payload)

            current_professor = ProfessorModel.get_professor_by_id(clean_data["current_id_professor"])
            if not current_professor:
                return {
                    "success": False,
                    "message": "El profesor que intenta modificar no existe.",
                }

            id_changed = clean_data["id_professor"] != clean_data["current_id_professor"]
            if id_changed and ProfessorModel.get_professor_by_id(clean_data["id_professor"]):
                return {
                    "success": False,
                    "message": "Ya existe un profesor con esa identificación.",
                }

            professor = ProfessorModel.update_professor(**clean_data)

            return {
                "success": True,
                "message": "Profesor modificado correctamente.",
                "professor": professor,
                "data": professor,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al modificar el profesor.",
            }

    @staticmethod
    def delete_professor(data: dict | str | None = None, **kwargs) -> dict:
        """
        Elimina permanentemente un profesor registrado.

        La eliminación solo se permite cuando el profesor no tiene cursos
        asignados. Esta regla protege la integridad académica del sistema:
        los cursos no deben eliminarse automáticamente al borrar un docente.
        """
        payload = ProfessorService._normalize_delete_payload(data, kwargs)

        try:
            id_professor = ProfessorService._validate_delete_payload(payload)

            professor = ProfessorModel.get_professor_by_id(id_professor)
            if not professor:
                return {
                    "success": False,
                    "message": "El profesor que intenta eliminar no existe.",
                }

            if ProfessorModel.has_assigned_courses(id_professor):
                return {
                    "success": False,
                    "message": (
                        "No se puede eliminar el profesor porque tiene cursos asignados. "
                        "Primero debe reasignar o eliminar esos cursos."
                    ),
                }

            deleted_professor = ProfessorModel.delete_professor(id_professor)

            return {
                "success": True,
                "message": "Profesor eliminado correctamente.",
                "professor": deleted_professor,
                "data": deleted_professor,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al eliminar el profesor.",
            }

    @staticmethod
    def get_professors() -> dict:
        try:
            professors = ProfessorModel.get_all_professors()

            return {
                "success": True,
                "message": "Profesores consultados correctamente.",
                "professors": professors,
                "data": professors,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los profesores.",
                "professors": [],
                "data": [],
            }

    @staticmethod
    def get_professor_by_id(id_professor: str) -> dict:
        try:
            id_professor = str(id_professor).strip()
            if not id_professor:
                return {
                    "success": False,
                    "message": "La identificación del profesor es obligatoria.",
                }

            professor = ProfessorModel.get_professor_by_id(id_professor)

            if not professor:
                return {
                    "success": False,
                    "message": "Profesor no encontrado.",
                }

            return {
                "success": True,
                "message": "Profesor encontrado.",
                "professor": professor,
                "data": professor,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el profesor.",
            }

    @staticmethod
    def get_professor_by_user_id(id_user: int | str) -> dict:
        """
        Consulta el perfil de profesor asociado a un usuario autenticado.

        Este método conecta el usuario del login con el registro real de
        professors, sin exponer consultas SQL en la interfaz gráfica.
        """
        try:
            id_user = ProfessorService._extract_user_id(id_user=id_user)
            professor = ProfessorModel.get_professor_by_user_id(id_user)

            if not professor:
                return {
                    "success": False,
                    "message": "No existe un perfil de profesor asociado a este usuario.",
                    "professor": None,
                    "data": None,
                }

            return {
                "success": True,
                "message": "Profesor encontrado.",
                "professor": professor,
                "professor_data": ProfessorService._professor_to_dict(professor),
                "data": professor,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "professor": None,
                "data": None,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el perfil del profesor.",
                "professor": None,
                "data": None,
            }

    @staticmethod
    def get_assigned_courses_by_user(user=None, id_user: int | str | None = None) -> dict:
        """
        Consulta los cursos asignados al profesor autenticado.

        Flujo de HU-24:
        User autenticado -> Professor asociado -> Cursos filtrados por id_professor.
        La GUI de profesores debe consumir este método y no consultar modelos ni
        base de datos directamente.
        """
        try:
            if not ProfessorService._user_has_professor_role(user):
                return {
                    "success": False,
                    "message": "El usuario autenticado no tiene permisos de profesor.",
                    "professor": None,
                    "professor_data": None,
                    "courses": [],
                    "entities": [],
                    "data": [],
                }

            id_user = ProfessorService._extract_user_id(user=user, id_user=id_user)
            professor = ProfessorModel.get_professor_by_user_id(id_user)

            if not professor:
                return {
                    "success": False,
                    "message": "No existe un perfil de profesor asociado a este usuario.",
                    "professor": None,
                    "professor_data": None,
                    "courses": [],
                    "entities": [],
                    "data": [],
                }

            courses = CourseModel.get_courses_by_professor_id(professor.id_professor)
            course_records = [ProfessorService._course_to_dict(course) for course in courses]

            return {
                "success": True,
                "message": "Cursos asignados consultados correctamente.",
                "professor": professor,
                "professor_data": ProfessorService._professor_to_dict(professor),
                "courses": course_records,
                "entities": courses,
                "data": course_records,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "professor": None,
                "professor_data": None,
                "courses": [],
                "entities": [],
                "data": [],
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los cursos asignados.",
                "professor": None,
                "professor_data": None,
                "courses": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def get_assigned_course_detail_by_user(user=None, id_user: int | str | None = None, code_course: str | None = None) -> dict:
        """
        Consulta el detalle de un curso asignado al profesor autenticado.

        Flujo de HU-25:
        User autenticado -> Professor asociado -> Curso filtrado por code_course
        e id_professor. La validación por profesor evita consultar cursos ajenos
        aunque se conozca el código del curso.
        """
        try:
            if not ProfessorService._user_has_professor_role(user):
                return {
                    "success": False,
                    "message": "El usuario autenticado no tiene permisos de profesor.",
                    "professor": None,
                    "professor_data": None,
                    "course": None,
                    "entity": None,
                    "data": None,
                }

            code_course = str(code_course or "").strip()
            if not code_course:
                raise ValueError("El código del curso es obligatorio para consultar el detalle.")

            id_user = ProfessorService._extract_user_id(user=user, id_user=id_user)
            professor = ProfessorModel.get_professor_by_user_id(id_user)

            if not professor:
                return {
                    "success": False,
                    "message": "No existe un perfil de profesor asociado a este usuario.",
                    "professor": None,
                    "professor_data": None,
                    "course": None,
                    "entity": None,
                    "data": None,
                }

            course = CourseModel.get_course_by_code_and_professor_id(
                code_course=code_course,
                id_professor=professor.id_professor,
            )

            if not course:
                return {
                    "success": False,
                    "message": "Curso no encontrado o no asignado al profesor autenticado.",
                    "professor": professor,
                    "professor_data": ProfessorService._professor_to_dict(professor),
                    "course": None,
                    "entity": None,
                    "data": None,
                }

            course_record = ProfessorService._course_to_dict(course)

            return {
                "success": True,
                "message": "Detalle del curso consultado correctamente.",
                "professor": professor,
                "professor_data": ProfessorService._professor_to_dict(professor),
                "course": course_record,
                "entity": course,
                "data": course_record,
            }

        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "professor": None,
                "professor_data": None,
                "course": None,
                "entity": None,
                "data": None,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el detalle del curso asignado.",
                "professor": None,
                "professor_data": None,
                "course": None,
                "entity": None,
                "data": None,
            }

    @staticmethod
    def search_professors_by_name(name: str) -> dict:
        try:
            name = str(name).strip().lower()
            if not name:
                return ProfessorService.get_professors()

            result = ProfessorService.get_professors()
            if not result.get("success"):
                return result

            professors = result.get("professors", [])
            filtered_professors = [
                professor
                for professor in professors
                if name in str(getattr(professor.user, "name", "")).lower()
            ]

            return {
                "success": True,
                "message": "Profesores filtrados correctamente.",
                "professors": filtered_professors,
                "data": filtered_professors,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al buscar profesores.",
                "professors": [],
                "data": [],
            }

    @staticmethod
    def _normalize_payload(data: dict | None, kwargs: dict) -> dict:
        payload = {}
        if isinstance(data, dict):
            payload.update(data)
        payload.update(kwargs)
        return payload

    @staticmethod
    def _normalize_delete_payload(data: dict | str | None, kwargs: dict) -> dict:
        payload = {}

        if isinstance(data, dict):
            payload.update(data)
        elif data not in (None, ""):
            payload["id_professor"] = data

        payload.update(kwargs)
        return payload

    @staticmethod
    def _validate_registration_payload(payload: dict) -> dict:
        id_professor = ProfessorService._read_first(
            payload,
            "id_professor",
            "identification",
            "document",
        )
        name = ProfessorService._read_first(payload, "name", "professor_name")
        password = ProfessorService._read_first(payload, "password")
        email = ProfessorService._read_first(payload, "email")
        birth_date = ProfessorService._read_first(payload, "birth_date", "date_of_birth")
        nationality = ProfessorService._read_first(payload, "nationality")
        professional_title = ProfessorService._read_first(
            payload,
            "professional_title",
            "title",
            "profession",
            "specialty",
        )

        required_fields = {
            "identificación": id_professor,
            "nombre": name,
            "contraseña": password,
            "correo electrónico": email,
            "fecha de nacimiento": birth_date,
            "nacionalidad": nationality,
            "título profesional": professional_title,
        }

        missing = [label for label, value in required_fields.items() if value in (None, "")]
        if missing:
            raise ValueError("Campos obligatorios faltantes: " + ", ".join(missing) + ".")

        id_professor = str(id_professor).strip()
        name = str(name).strip()
        password = str(password).strip()
        email = str(email).strip()
        nationality = str(nationality).strip()
        professional_title = str(professional_title).strip()
        birth_date = ProfessorService._parse_date(birth_date)

        if len(id_professor) < 3:
            raise ValueError("La identificación del profesor debe tener al menos 3 caracteres.")

        if len(name) < 3:
            raise ValueError("El nombre del profesor debe tener al menos 3 caracteres.")

        if len(password) < 4:
            raise ValueError("La contraseña inicial debe tener al menos 4 caracteres.")

        if not ProfessorService.EMAIL_PATTERN.match(email):
            raise ValueError("El correo electrónico no tiene un formato válido.")

        if birth_date > date.today():
            raise ValueError("La fecha de nacimiento no puede ser posterior a la fecha actual.")

        if len(nationality) < 3:
            raise ValueError("La nacionalidad debe tener al menos 3 caracteres.")

        if len(professional_title) < 3:
            raise ValueError("El título profesional debe tener al menos 3 caracteres.")

        return {
            "id_professor": id_professor,
            "name": name,
            "password": password,
            "email": email,
            "birth_date": birth_date,
            "nationality": nationality,
            "professional_title": professional_title,
        }

    @staticmethod
    def _validate_update_payload(payload: dict) -> dict:
        current_id_professor = ProfessorService._read_first(
            payload,
            "current_id_professor",
            "original_id_professor",
            "old_id_professor",
            "selected_id_professor",
        )
        id_professor = ProfessorService._read_first(
            payload,
            "id_professor",
            "identification",
            "document",
        )
        name = ProfessorService._read_first(payload, "name", "professor_name")
        password = payload.get("password")
        email = ProfessorService._read_first(payload, "email")
        birth_date = ProfessorService._read_first(payload, "birth_date", "date_of_birth")
        nationality = ProfessorService._read_first(payload, "nationality")
        professional_title = ProfessorService._read_first(
            payload,
            "professional_title",
            "title",
            "profession",
            "specialty",
        )

        if id_professor in (None, ""):
            id_professor = current_id_professor

        required_fields = {
            "identificación actual": current_id_professor,
            "identificación": id_professor,
            "nombre": name,
            "correo electrónico": email,
            "fecha de nacimiento": birth_date,
            "nacionalidad": nationality,
            "título profesional": professional_title,
        }

        missing = [label for label, value in required_fields.items() if value in (None, "")]
        if missing:
            raise ValueError("Campos obligatorios faltantes: " + ", ".join(missing) + ".")

        current_id_professor = str(current_id_professor).strip()
        id_professor = str(id_professor).strip()
        name = str(name).strip()
        email = str(email).strip()
        nationality = str(nationality).strip()
        professional_title = str(professional_title).strip()
        birth_date = ProfessorService._parse_date(birth_date)

        clean_password = None
        if password not in (None, ""):
            clean_password = str(password).strip()
            if clean_password == "":
                clean_password = None

        if len(current_id_professor) < 3:
            raise ValueError("La identificación actual del profesor debe tener al menos 3 caracteres.")

        if len(id_professor) < 3:
            raise ValueError("La identificación del profesor debe tener al menos 3 caracteres.")

        if len(name) < 3:
            raise ValueError("El nombre del profesor debe tener al menos 3 caracteres.")

        if clean_password is not None and len(clean_password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres.")

        if not ProfessorService.EMAIL_PATTERN.match(email):
            raise ValueError("El correo electrónico no tiene un formato válido.")

        if birth_date > date.today():
            raise ValueError("La fecha de nacimiento no puede ser posterior a la fecha actual.")

        if len(nationality) < 3:
            raise ValueError("La nacionalidad debe tener al menos 3 caracteres.")

        if len(professional_title) < 3:
            raise ValueError("El título profesional debe tener al menos 3 caracteres.")

        return {
            "current_id_professor": current_id_professor,
            "id_professor": id_professor,
            "name": name,
            "password": clean_password,
            "email": email,
            "birth_date": birth_date,
            "nationality": nationality,
            "professional_title": professional_title,
        }

    @staticmethod
    def _validate_delete_payload(payload: dict) -> str:
        id_professor = ProfessorService._read_first(
            payload,
            "id_professor",
            "current_id_professor",
            "selected_id_professor",
            "identification",
            "document",
        )

        if id_professor in (None, ""):
            raise ValueError("La identificación del profesor es obligatoria para eliminar el registro.")

        id_professor = str(id_professor).strip()

        if not id_professor:
            raise ValueError("La identificación del profesor es obligatoria para eliminar el registro.")

        if len(id_professor) < 3:
            raise ValueError("La identificación del profesor debe tener al menos 3 caracteres.")

        return id_professor

    @staticmethod
    def _read_first(payload: dict, *keys):
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _parse_date(value) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        value = str(value).strip()
        for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                pass

        raise ValueError("La fecha de nacimiento debe tener formato YYYY-MM-DD.")

    @staticmethod
    def _extract_user_id(user=None, id_user: int | str | None = None) -> int:
        if id_user in (None, ""):
            if isinstance(user, dict):
                id_user = ProfessorService._read_first(user, "id_user", "user_id")
            elif hasattr(user, "id_user"):
                id_user = getattr(user, "id_user")
            else:
                id_user = user

        if id_user in (None, ""):
            raise ValueError("El usuario autenticado es obligatorio.")

        try:
            return int(id_user)
        except (TypeError, ValueError):
            raise ValueError("El identificador del usuario autenticado no es válido.")

    @staticmethod
    def _user_has_professor_role(user) -> bool:
        if user is None:
            return True

        role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
        if role is None:
            return True

        role_name = str(getattr(role, "name", "")).upper()
        role_value = str(getattr(role, "value", role)).lower()

        return role_name == "PROFESSOR" or role_value == "professor"

    @staticmethod
    def _professor_to_dict(professor) -> dict:
        user = getattr(professor, "user", None)

        return {
            "id_professor": getattr(professor, "id_professor", ""),
            "professional_title": getattr(professor, "professional_title", ""),
            "id_user": getattr(user, "id_user", ""),
            "name": getattr(user, "name", ""),
            "email": getattr(user, "email", ""),
            "birth_date": getattr(user, "birth_date", ""),
            "nationality": getattr(user, "nationality", ""),
        }

    @staticmethod
    def _course_to_dict(course) -> dict:
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
