import re
from datetime import date, datetime

from ca_program.models.professor_model import ProfessorModel


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
    def _normalize_payload(data: dict | None, kwargs: dict) -> dict:
        payload = {}
        if isinstance(data, dict):
            payload.update(data)
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

    create_professor = register_professor
    add_professor = register_professor
    save_professor = register_professor
    register = register_professor

    list_professors = get_professors
    get_all_professors = get_professors
    consult_professors = get_professors
    get_all = get_professors
