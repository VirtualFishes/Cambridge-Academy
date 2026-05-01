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
                "course": course,
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
    def update_course(data: dict | None = None, **kwargs) -> dict:
        """
        Modifica la información de un curso registrado.

        El código del curso debe llegar en code_course, current_code_course,
        selected_code_course o course_code. El código se usa como identificador
        estable del registro y no se modifica desde esta operación.
        """
        payload = CourseService._normalize_payload(data, kwargs)

        try:
            clean_data = CourseService._validate_update_payload(payload)
            code_course = clean_data.pop("code_course")

            if not CourseModel.course_exists(code_course):
                return {
                    "success": False,
                    "message": "El curso que intenta modificar no existe.",
                }

            if not CourseModel.professor_exists(clean_data["id_professor"]):
                return {
                    "success": False,
                    "message": "El profesor asignado no existe.",
                }

            course = CourseModel.update_course(
                code_course=code_course,
                **clean_data,
            )
            course_data = CourseService._course_to_dict(course)

            return {
                "success": True,
                "message": "Curso modificado correctamente.",
                "course": course,
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
                "message": "Ocurrió un error al modificar el curso.",
            }


    @staticmethod
    def delete_course(code_course: int | str | dict | None = None, data: dict | None = None, **kwargs) -> dict:
        """
        Elimina permanentemente un curso registrado.

        Acepta el código del curso como argumento directo o dentro de un
        diccionario usando claves como code_course, selected_code_course o
        course_code. La eliminación real de registros asociados se delega al
        modelo para mantener la capa de servicio libre de SQL.
        """
        if isinstance(code_course, dict) and data is None:
            data = code_course
            code_course = None

        payload = CourseService._normalize_payload(data, kwargs)
        if code_course not in (None, ""):
            payload["code_course"] = code_course

        try:
            code_course = CourseService._validate_delete_payload(payload)

            if not CourseModel.course_exists(code_course):
                return {
                    "success": False,
                    "message": "El curso que intenta eliminar no existe.",
                }

            course = CourseModel.delete_course(code_course)
            course_data = CourseService._course_to_dict(course)

            return {
                "success": True,
                "message": "Curso eliminado correctamente.",
                "course": course,
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
                "message": "Ocurrió un error al eliminar el curso.",
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
    def get_students_by_course(code_course: int | str) -> dict:
        try:
            code_course = str(code_course).strip()
            if not code_course:
                return {
                    "success": False,
                    "message": "El código del curso es obligatorio.",
                    "students": [],
                    "data": [],
                }

            if not CourseModel.get_course_by_code(code_course):
                return {
                    "success": False,
                    "message": "Curso no encontrado.",
                    "students": [],
                    "data": [],
                }

            students = CourseModel.get_students_by_course(code_course)
            student_records = [CourseService._student_to_dict(student) for student in students]

            return {
                "success": True,
                "message": "Estudiantes del curso consultados correctamente.",
                "students": student_records,
                "entities": students,
                "data": student_records,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar los estudiantes del curso.",
                "students": [],
                "entities": [],
                "data": [],
            }

    @staticmethod
    def search_courses_by_name(name: str) -> dict:
        try:
            name = str(name).strip().lower()
            if not name:
                return CourseService.get_courses()

            result = CourseService.get_courses()
            if not result.get("success"):
                return result

            courses = result.get("courses", [])
            filtered_courses = [
                course
                for course in courses
                if name in str(course.get("name", "")).lower()
            ]

            return {
                "success": True,
                "message": "Cursos filtrados correctamente.",
                "courses": filtered_courses,
                "data": filtered_courses,
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al buscar cursos.",
                "courses": [],
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
    def _validate_update_payload(payload: dict) -> dict:
        code_course = CourseService._read_first(
            payload,
            "code_course",
            "current_code_course",
            "selected_code_course",
            "course_code",
            "current_course_code",
            "selected_course_code",
        )

        if code_course in (None, ""):
            raise ValueError("El código del curso es obligatorio para modificar el registro.")

        code_course = str(code_course).strip()
        if not code_course:
            raise ValueError("El código del curso es obligatorio para modificar el registro.")

        clean_data = CourseService._validate_registration_payload(payload)
        clean_data["code_course"] = code_course
        return clean_data


    @staticmethod
    def _validate_delete_payload(payload: dict) -> str:
        code_course = CourseService._read_first(
            payload,
            "code_course",
            "current_code_course",
            "selected_code_course",
            "course_code",
            "current_course_code",
            "selected_course_code",
        )

        if code_course in (None, ""):
            raise ValueError("El código del curso es obligatorio para eliminar el registro.")

        code_course = str(code_course).strip()
        if not code_course:
            raise ValueError("El código del curso es obligatorio para eliminar el registro.")

        return code_course

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
            parsed_value = int(value)
        except (TypeError, ValueError):
            raise ValueError(error_message)

        return parsed_value

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

    @staticmethod
    def _student_to_dict(student) -> dict:
        user = getattr(student, "user", None)

        return {
            "id_student": getattr(student, "id_student", ""),
            "name": getattr(user, "name", ""),
            "email": getattr(user, "email", ""),
            "birth_date": getattr(user, "birth_date", ""),
            "nationality": getattr(user, "nationality", ""),
        }

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
