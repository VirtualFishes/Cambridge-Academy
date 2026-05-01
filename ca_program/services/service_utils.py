"""
Utilidades compartidas para la capa de servicios.

Este módulo evita repetir validaciones, normalización de datos y conversión de
entidades a diccionarios en cada servicio. No accede a la base de datos ni
contiene reglas de persistencia; su responsabilidad es apoyar a los servicios
con tareas transversales y simples.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

from ca_program.entities.fixed_values import AcademicStatus


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")

NAME_SEPARATORS = {" ", "-", "'", "’"}


def normalize_payload(data: dict | None = None, kwargs: dict | None = None) -> dict:
    """Combina un diccionario opcional y argumentos nombrados en un solo payload."""
    payload: dict = {}
    if isinstance(data, dict):
        payload.update(data)
    if kwargs:
        payload.update(kwargs)
    return payload


def normalize_delete_payload(
    data: dict | str | int | None = None,
    kwargs: dict | None = None,
    id_key: str = "id",
) -> dict:
    """Normaliza entradas de eliminación recibidas como ID directo o diccionario."""
    payload: dict = {}
    if isinstance(data, dict):
        payload.update(data)
    elif data not in (None, ""):
        payload[id_key] = data

    if kwargs:
        payload.update(kwargs)

    return payload


def read_first(payload: dict, *keys: str) -> Any:
    """Retorna el primer valor no vacío encontrado para una lista de claves."""
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_spaces(value: Any) -> str:
    """Convierte un valor a texto y elimina espacios repetidos."""
    return " ".join(str(value or "").strip().split())


def clean_text(value: Any, field_label: str, min_length: int = 1) -> str:
    """Valida y limpia un texto obligatorio."""
    if value in (None, ""):
        raise ValueError(f"{field_label} es obligatorio.")

    clean_value = normalize_spaces(value)

    if len(clean_value) < min_length:
        raise ValueError(f"{field_label} debe tener al menos {min_length} caracteres.")

    return clean_value


def validate_required_fields(fields: dict[str, Any]) -> None:
    """Lanza ValueError con un listado legible de campos faltantes."""
    missing = [label for label, value in fields.items() if value in (None, "")]
    if missing:
        raise ValueError("Campos obligatorios faltantes: " + ", ".join(missing) + ".")


def validate_numeric_id(
    value: Any,
    field_label: str = "La identificación",
    min_length: int = 3,
    max_length: int | None = None,
) -> str:
    """
    Valida identificaciones compuestas únicamente por números.

    Úsese para documentos de estudiantes, profesores o usuarios cuando la regla
    del sistema indique que no se aceptan letras ni símbolos.
    """
    clean_value = clean_text(value, field_label, min_length=min_length)

    if not clean_value.isdigit():
        raise ValueError(f"{field_label} debe contener solo números.")

    if max_length is not None and len(clean_value) > max_length:
        raise ValueError(f"{field_label} no debe superar {max_length} caracteres.")

    return clean_value


def validate_person_name(
    value: Any,
    field_label: str = "El nombre",
    min_length: int = 3,
) -> str:
    """
    Valida nombres de personas.

    Acepta letras, espacios, tildes, ñ, guiones y apóstrofes.
    No acepta números ni símbolos especiales.
    """
    clean_value = clean_text(value, field_label, min_length=min_length)

    if not any(character.isalpha() for character in clean_value):
        raise ValueError(f"{field_label} debe contener letras.")

    for character in clean_value:
        if not character.isalpha() and character not in NAME_SEPARATORS:
            raise ValueError(f"{field_label} solo debe contener letras y espacios.")

    return clean_value


def validate_alpha_text(
    value: Any,
    field_label: str,
    min_length: int = 3,
) -> str:
    """
    Valida textos compuestos principalmente por letras.

    Es útil para nacionalidad u otros campos donde no deben aparecer números.
    """
    clean_value = clean_text(value, field_label, min_length=min_length)

    for character in clean_value:
        if not character.isalpha() and character not in NAME_SEPARATORS:
            raise ValueError(f"{field_label} solo debe contener letras y espacios.")

    return clean_value


def validate_password_required(
    password: Any,
    field_label: str = "La contraseña",
    min_length: int = 4,
) -> str:
    """Valida una contraseña obligatoria."""
    clean_password = clean_text(password, field_label, min_length=min_length)
    return clean_password


def parse_date(
    value: Any,
    error_message: str,
    allow_future: bool = True,
    future_error_message: str | None = None,
) -> date:
    """Convierte fechas de la GUI a date, aceptando formatos comunes."""
    if isinstance(value, datetime):
        parsed_date = value.date()
    elif isinstance(value, date):
        parsed_date = value
    else:
        text_value = str(value).strip()
        parsed_date = None

        for date_format in DEFAULT_DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(text_value, date_format).date()
                break
            except ValueError:
                continue

        if parsed_date is None:
            raise ValueError(error_message)

    if not allow_future and parsed_date > date.today():
        raise ValueError(
            future_error_message
            or "La fecha no puede ser posterior a la fecha actual."
        )

    return parsed_date


def parse_float(
    value: Any,
    error_message: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Convierte un valor a float y valida límites opcionales."""
    if isinstance(value, str):
        value = value.strip().replace(",", ".")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc

    if minimum is not None and number < minimum:
        raise ValueError(f"El valor no puede ser menor que {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"El valor no puede ser mayor que {maximum}.")

    return number


def parse_int(
    value: Any,
    error_message: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Convierte un valor a int y valida límites opcionales."""
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc

    if minimum is not None and number < minimum:
        raise ValueError(f"El valor no puede ser menor que {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"El valor no puede ser mayor que {maximum}.")

    return number


def validate_email(email: str) -> str:
    """Valida formato básico de correo electrónico."""
    clean_email = clean_text(email, "El correo electrónico", min_length=5)

    if not EMAIL_PATTERN.match(clean_email):
        raise ValueError("El correo electrónico no tiene un formato válido.")

    return clean_email


def clean_optional_password(password: Any, min_length: int = 4) -> str | None:
    """Normaliza contraseña opcional para operaciones de modificación."""
    if password in (None, ""):
        return None

    clean_password = str(password).strip()
    if not clean_password:
        return None

    if len(clean_password) < min_length:
        raise ValueError(f"La contraseña debe tener al menos {min_length} caracteres.")

    return clean_password


def validate_required_id(value: Any, error_message: str) -> str:
    """
    Extrae, limpia y valida identificadores recibidos como valor, entidad o dict.

    Esta función sigue siendo genérica. No exige que el ID sea numérico porque
    también se usa para códigos de curso, matrículas u otros identificadores.
    """
    clean_value = extract_id_value(value)

    if clean_value is None:
        raise ValueError(error_message)

    clean_value = str(clean_value).strip()
    if not clean_value:
        raise ValueError(error_message)

    return clean_value


def extract_id_value(value: Any) -> Any:
    """Extrae identificadores comunes desde diccionarios o entidades simples."""
    if isinstance(value, dict):
        for key in (
            "id_user",
            "user_id",
            "id_student",
            "student_id",
            "id_professor",
            "professor_id",
            "code_course",
            "course_code",
            "id_enrollment",
            "id_grade",
            "id",
        ):
            if value.get(key) not in (None, ""):
                return value.get(key)
        return None

    for attribute in (
        "id_user",
        "user_id",
        "id_student",
        "student_id",
        "id_professor",
        "professor_id",
        "code_course",
        "course_code",
        "id_enrollment",
        "id_grade",
        "id",
    ):
        if hasattr(value, attribute):
            attr_value = getattr(value, attribute)
            if attr_value not in (None, ""):
                return attr_value

    return value


def extract_user_id(user: Any = None, id_user: int | str | None = None) -> int:
    """Obtiene el id_user desde un argumento directo, entidad User o diccionario."""
    if id_user in (None, ""):
        if isinstance(user, dict):
            id_user = read_first(user, "id_user", "user_id")
        elif hasattr(user, "id_user"):
            id_user = getattr(user, "id_user")
        else:
            id_user = user

    if id_user in (None, ""):
        raise ValueError("El usuario autenticado es obligatorio.")

    try:
        clean_id_user = int(id_user)
    except (TypeError, ValueError) as exc:
        raise ValueError("El identificador del usuario autenticado no es válido.") from exc

    if clean_id_user <= 0:
        raise ValueError("El identificador del usuario autenticado no es válido.")

    return clean_id_user


def role_matches(user: Any, allowed_values: Iterable[str], allow_missing: bool = True) -> bool:
    """Verifica si el rol del usuario coincide con alguno de los roles permitidos."""
    if user is None:
        return allow_missing

    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    if role is None:
        return allow_missing

    allowed = {str(value).strip().lower() for value in allowed_values}
    role_name = str(getattr(role, "name", "")).strip().lower()
    role_value = str(getattr(role, "value", role)).strip().lower()

    return role_name in allowed or role_value in allowed


def status_to_value(status: Any) -> str:
    """Convierte enums de estado a su valor persistible o representable."""
    value = getattr(status, "value", status)
    return str(value).strip().lower()


def academic_status_to_label(status: Any) -> str:
    """Convierte el estado académico en una etiqueta legible para la GUI."""
    value = status_to_value(status)

    if value == AcademicStatus.PASSED.value:
        return "Aprobado"
    if value == AcademicStatus.FAILED.value:
        return "Reprobado"
    if value == "pending":
        return "Pendiente"

    return "Sin estado"


def response(success: bool, message: str, **payload: Any) -> dict:
    """Construye respuestas homogéneas para la GUI y otras capas consumidoras."""
    result = {
        "success": success,
        "message": message,
    }
    result.update(payload)
    return result


def error_response(message: str, **payload: Any) -> dict:
    """Atajo semántico para respuestas de error controlado."""
    return response(False, message, **payload)


def success_response(message: str, **payload: Any) -> dict:
    """Atajo semántico para respuestas exitosas."""
    return response(True, message, **payload)


def unexpected_error_response(exception: Exception, message: str, **payload: Any) -> dict:
    """Registra un error técnico y retorna un mensaje seguro para la interfaz."""
    print(exception)
    return error_response(message, **payload)


def user_to_dict(user: Any) -> dict:
    """Convierte una entidad User en diccionario de presentación."""
    if user is None:
        return {}

    role = getattr(user, "role", "")

    return {
        "id_user": getattr(user, "id_user", ""),
        "name": getattr(user, "name", ""),
        "role": status_to_value(role),
        "email": getattr(user, "email", ""),
        "birth_date": getattr(user, "birth_date", ""),
        "nationality": getattr(user, "nationality", ""),
    }


def student_to_dict(student: Any) -> dict:
    """Convierte una entidad Student en diccionario."""
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


def professor_to_dict(professor: Any) -> dict:
    """Convierte una entidad Professor en diccionario."""
    if professor is None:
        return {}

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


def course_to_dict(course: Any) -> dict:
    """Convierte una entidad Course en diccionario de presentación."""
    if course is None:
        return {}

    professor = getattr(course, "professor", None)
    professor_data = professor_to_dict(professor)

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
        "id_professor": professor_data.get("id_professor", ""),
        "professor": professor_data,
        "students": getattr(course, "enrolled_students", 0),
        "enrolled_students": getattr(course, "enrolled_students", 0),
    }


def enrollment_to_dict(enrollment: Any) -> dict:
    """Convierte una entidad Enrollment en diccionario."""
    if enrollment is None:
        return {}

    return {
        "id_enrollment": getattr(enrollment, "id_enrollment", ""),
        "student": student_to_dict(getattr(enrollment, "student", None)),
        "course": course_to_dict(getattr(enrollment, "course", None)),
    }


def receipt_to_dict(receipt: Any) -> dict:
    """Convierte una entidad Receipt en diccionario."""
    if receipt is None:
        return {}

    status = getattr(receipt, "status", "")

    return {
        "id_receipt": getattr(receipt, "id_receipt", ""),
        "issue_date": getattr(receipt, "issue_date", ""),
        "due_date": getattr(receipt, "due_date", ""),
        "amount": getattr(receipt, "amount", 0),
        "status": status_to_value(status),
        "enrollment": enrollment_to_dict(getattr(receipt, "enrollment", None)),
    }


def payment_to_dict(payment: Any) -> dict:
    """Convierte una entidad Payment en diccionario."""
    if payment is None:
        return {}

    return {
        "id_payment": getattr(payment, "id_payment", ""),
        "payment_date": getattr(payment, "payment_date", ""),
        "payment_method": status_to_value(getattr(payment, "payment_method", "")),
        "receipt": receipt_to_dict(getattr(payment, "receipt", None)),
    }
