from datetime import date, datetime
from typing import Any

from ca_program.models.course_model import CourseModel


class CourseService:

    @staticmethod
    def register_course(data: dict | None = None, **kwargs) -> dict:
        payload = CourseService._normalize_payload(data, kwargs)

        try:
            clean_data = CourseService._validate_registration_payload(payload)

            if not CourseModel.professor_exists(clean_data["id_professor"]):
                return {
                    "success": False,
                    "message": "El profesor asignado no existe.",
                }

            course = CourseModel.create_course(**clean_data)
            course_data = CourseService._course_to_dict(course)

            return {
                "success": True,
                "message": "Curso registrado correctamente.",
                "course": course_data,
                "entity": course,
                "data": course_data,
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
                "message": "Ocurrió un error al registrar el curso.",
            }

    @staticmethod
    def get_courses() -> dict:
        try:
            courses = CourseModel.get_all_courses()
            course_records = [CourseService._course_to_dict(course) for course in courses]

            return {
                "success": True,
                "message": "Cursos consultados correctamente.",
                "courses": course_records,
                "entities": courses,
                "data": course_records,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los cursos.",
                "courses": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def get_course_by_code(code_course: int | str) -> dict:
        try:
            code_course = str(code_course).strip()
            if not code_course:
                return {
                    "success": False,
                    "message": "El código del curso es obligatorio.",
                }

            course = CourseModel.get_course_by_code(code_course)

            if not course:
                return {
                    "success": False,
                    "message": "Curso no encontrado.",
                }

            course_data = CourseService._course_to_dict(course)

            return {
                "success": True,
                "message": "Curso encontrado.",
                "course": course_data,
                "entity": course,
                "data": course_data,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el curso.",
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
        name = CourseService._read_first(payload, "name", "course_name")
        description = CourseService._read_first(payload, "description")
        price = CourseService._read_first(payload, "price")
        duration_days = CourseService._read_first(payload, "duration_days", "duration")
        intensity_hours = CourseService._read_first(payload, "intensity_hours", "intensity")
        schedule = CourseService._read_first(payload, "schedule")
        location = CourseService._read_first(payload, "location")
        start_date = CourseService._read_first(payload, "start_date")
        end_date = CourseService._read_first(payload, "end_date")
        id_professor = CourseService._read_first(payload, "id_professor", "professor_id")

        required_fields = {
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

        missing = [label for label, value in required_fields.items() if value in (None, "")]
        if missing:
            raise ValueError("Campos obligatorios faltantes: " + ", ".join(missing) + ".")

        name = str(name).strip()
        description = str(description).strip()
        schedule = str(schedule).strip()
        location = str(location).strip()
        id_professor = str(id_professor).strip()
        price = CourseService._parse_float(price, "El precio debe ser un número válido.")
        duration_days = CourseService._parse_int(duration_days, "La duración en días debe ser un número entero válido.")
        intensity_hours = CourseService._parse_int(intensity_hours, "La intensidad horaria debe ser un número entero válido.")
        start_date = CourseService._parse_date(start_date, "La fecha de inicio debe tener formato YYYY-MM-DD.")
        end_date = CourseService._parse_date(end_date, "La fecha de finalización debe tener formato YYYY-MM-DD.")

        if len(name) < 3:
            raise ValueError("El nombre del curso debe tener al menos 3 caracteres.")

        if len(description) < 5:
            raise ValueError("La descripción del curso debe tener al menos 5 caracteres.")

        if price < 0:
            raise ValueError("El precio del curso no puede ser negativo.")

        if duration_days <= 0:
            raise ValueError("La duración del curso debe ser mayor que cero.")

        if intensity_hours <= 0:
            raise ValueError("La intensidad horaria debe ser mayor que cero.")

        if len(schedule) < 3:
            raise ValueError("El horario del curso debe tener al menos 3 caracteres.")

        if len(location) < 3:
            raise ValueError("La ubicación del curso debe tener al menos 3 caracteres.")

        if end_date < start_date:
            raise ValueError("La fecha de finalización no puede ser anterior a la fecha de inicio.")

        if len(id_professor) < 3:
            raise ValueError("La identificación del profesor asignado debe tener al menos 3 caracteres.")

        return {
            "name": name,
            "description": description,
            "price": price,
            "duration_days": duration_days,
            "intensity_hours": intensity_hours,
            "schedule": schedule,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "id_professor": id_professor,
        }

    @staticmethod
    def _read_first(payload: dict, *keys):
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _parse_float(value: Any, error_message: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(error_message)

    @staticmethod
    def _parse_int(value: Any, error_message: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(error_message)

    @staticmethod
    def _parse_date(value: Any, error_message: str) -> date:
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

        raise ValueError(error_message)

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

    create_course = register_course
    add_course = register_course
    save_course = register_course
    register = register_course

    list_courses = get_courses
    get_all_courses = get_courses
    consult_courses = get_courses
    get_all = get_courses
