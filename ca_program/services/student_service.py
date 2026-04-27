import re
from datetime import date, datetime

from ca_program.models.student_model import StudentModel


class StudentService:
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    @staticmethod
    def register_student(data: dict | None = None, **kwargs) -> dict:
        payload = StudentService._normalize_payload(data, kwargs)

        try:
            clean_data = StudentService._validate_registration_payload(payload)

            if StudentModel.get_student_by_id(clean_data["id_student"]):
                return {
                    "success": False,
                    "message": "Ya existe un estudiante con esa identificación.",
                }

            if StudentModel.email_exists(clean_data["email"]):
                return {
                    "success": False,
                    "message": "Ya existe un usuario registrado con ese correo electrónico.",
                }

            student = StudentModel.create_student(**clean_data)

            return {
                "success": True,
                "message": "Estudiante registrado correctamente.",
                "student": student,
                "data": student,
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
                "message": "Ocurrió un error al registrar el estudiante.",
            }

    @staticmethod
    def get_students() -> dict:
        try:
            students = StudentModel.get_all_students()

            return {
                "success": True,
                "message": "Estudiantes consultados correctamente.",
                "students": students,
                "data": students,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los estudiantes.",
                "students": [],
                "data": [],
            }

    @staticmethod
    def get_student_by_id(id_student: str) -> dict:
        try:
            id_student = str(id_student).strip()
            if not id_student:
                return {
                    "success": False,
                    "message": "La identificación del estudiante es obligatoria.",
                }

            student = StudentModel.get_student_by_id(id_student)

            if not student:
                return {
                    "success": False,
                    "message": "Estudiante no encontrado.",
                }

            return {
                "success": True,
                "message": "Estudiante encontrado.",
                "student": student,
                "data": student,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el estudiante.",
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
        id_student = StudentService._read_first(payload, "id_student", "identification", "document")
        name = StudentService._read_first(payload, "name", "student_name")
        password = StudentService._read_first(payload, "password")
        email = StudentService._read_first(payload, "email")
        birth_date = StudentService._read_first(payload, "birth_date", "date_of_birth")
        nationality = StudentService._read_first(payload, "nationality")

        required_fields = {
            "identificación": id_student,
            "nombre": name,
            "contraseña": password,
            "correo electrónico": email,
            "fecha de nacimiento": birth_date,
            "nacionalidad": nationality,
        }

        missing = [label for label, value in required_fields.items() if value in (None, "")]
        if missing:
            raise ValueError("Campos obligatorios faltantes: " + ", ".join(missing) + ".")

        id_student = str(id_student).strip()
        name = str(name).strip()
        password = str(password).strip()
        email = str(email).strip()
        nationality = str(nationality).strip()
        birth_date = StudentService._parse_date(birth_date)

        if len(name) < 3:
            raise ValueError("El nombre del estudiante debe tener al menos 3 caracteres.")

        if not StudentService.EMAIL_PATTERN.match(email):
            raise ValueError("El correo electrónico no tiene un formato válido.")

        if birth_date > date.today():
            raise ValueError("La fecha de nacimiento no puede ser posterior a la fecha actual.")

        return {
            "id_student": id_student,
            "name": name,
            "password": password,
            "email": email,
            "birth_date": birth_date,
            "nationality": nationality,
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

    create_student = register_student
    add_student = register_student
    save_student = register_student
    register = register_student

    list_students = get_students
    get_all_students = get_students
    consult_students = get_students
    get_all = get_students
