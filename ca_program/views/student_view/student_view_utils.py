"""
Utilidades compartidas para las vistas del submódulo student_view.

Este módulo centraliza operaciones de presentación: lectura segura de datos,
formateo visible, normalización de estados y limpieza de layouts. No consulta
servicios, modelos ni base de datos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


STATUS_NOT_ENROLLED = "NO_INSCRITO"
STATUS_PENDING_PAYMENT = "PENDIENTE_DE_PAGO"
STATUS_ENROLLED = "INSCRITO"
STATUS_EXPIRED = "VENCIDO"
STATUS_UNAVAILABLE = "ESTADO_NO_DISPONIBLE"


def clean_text(value: Any, default: str = "") -> str:
    """Convierte un valor a texto visible sin exponer None ni cadenas vacías."""
    if value in (None, ""):
        return default

    text = str(value).strip()
    return text if text else default


def enum_value(value: Any) -> Any:
    """Retorna value.value cuando el objeto recibido es un Enum."""
    return getattr(value, "value", value)


def read_mapping_value(mapping: Any, *keys: str, default: Any = "") -> Any:
    """Lee el primer valor disponible dentro de un diccionario simple."""
    if not isinstance(mapping, dict):
        return default

    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return default


def read_object_value(source: Any, key: str, default: Any = "") -> Any:
    """Lee un campo desde diccionario u objeto."""
    if source in (None, ""):
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    return getattr(source, key, default)


def get_user_id(user: Any) -> Any:
    """Obtiene el id_user de un usuario autenticado."""
    if isinstance(user, dict):
        return read_mapping_value(user, "id_user", "user_id", default=None)

    return getattr(user, "id_user", None)


def get_course_code(course: Any) -> str:
    """Obtiene el código de curso aceptando las claves usadas en la GUI."""
    value = read_mapping_value(
        course,
        "code_course",
        "course_code",
        "code",
        "id",
        default="",
    )
    return clean_text(value)


def get_course_name(course: Any, default: str = "el curso seleccionado") -> str:
    """Obtiene el nombre visible de un curso."""
    return clean_text(read_mapping_value(course, "name", "course_name", default=""), default)


def normalize_enrollment_status(status: Any) -> str:
    """Normaliza estados de inscripción a las constantes visibles del estudiante."""
    status_text = clean_text(enum_value(status), STATUS_NOT_ENROLLED).upper()

    aliases = {
        "NOT_ENROLLED": STATUS_NOT_ENROLLED,
        "NO INSCRITO": STATUS_NOT_ENROLLED,
        "DISPONIBLE": STATUS_NOT_ENROLLED,
        STATUS_NOT_ENROLLED: STATUS_NOT_ENROLLED,
        "PENDING_PAYMENT": STATUS_PENDING_PAYMENT,
        "PENDIENTE": STATUS_PENDING_PAYMENT,
        "PENDIENTE DE PAGO": STATUS_PENDING_PAYMENT,
        STATUS_PENDING_PAYMENT: STATUS_PENDING_PAYMENT,
        "ENROLLED": STATUS_ENROLLED,
        "CONFIRMADO": STATUS_ENROLLED,
        STATUS_ENROLLED: STATUS_ENROLLED,
        "EXPIRED": STATUS_EXPIRED,
        STATUS_EXPIRED: STATUS_EXPIRED,
        STATUS_UNAVAILABLE: STATUS_UNAVAILABLE,
    }
    return aliases.get(status_text, status_text)


def enrollment_status_label(status: Any) -> str:
    """Convierte un estado de inscripción en etiqueta comprensible."""
    normalized = normalize_enrollment_status(status)

    labels = {
        STATUS_ENROLLED: "Inscrito",
        STATUS_PENDING_PAYMENT: "Pendiente de pago",
        STATUS_EXPIRED: "Vencido",
        STATUS_UNAVAILABLE: "Disponible",
        STATUS_NOT_ENROLLED: "Disponible",
    }
    return labels.get(normalized, "Disponible")


def read_float(value: Any, default: float = 0.0) -> float:
    """Convierte un valor a float aceptando coma decimal."""
    if isinstance(value, str):
        value = value.strip().replace(",", ".")

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_int(value: Any, default: int = 0) -> int:
    """Convierte un valor a entero de forma tolerante."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def format_price(value: Any, default: str = "No registrado") -> str:
    """Formatea un valor monetario en pesos para la GUI."""
    amount = read_float(value, -1.0)
    if amount <= 0:
        return default

    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"$ {formatted}"


def format_currency(value: Any) -> str:
    """Formatea moneda con dos decimales cuando son necesarios."""
    amount = read_float(value, 0.0)
    if float(amount).is_integer():
        return f"$ {int(amount)}"
    return f"$ {amount:,.2f}"


def format_date(value: Any, default: str = "No registrada") -> str:
    """Formatea fechas para presentación al estudiante."""
    if value in (None, ""):
        return default

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    text = str(value).strip()
    if not text:
        return default

    for date_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text[:19], date_format).strftime("%d/%m/%Y")
        except ValueError:
            continue

    return text


def format_unit_count(value: Any, singular: str, plural: str, default: str = "No registrada") -> str:
    """Formatea una cantidad con su unidad en singular o plural."""
    number = read_int(value, -1)
    if number < 0:
        return default

    unit = singular if number == 1 else plural
    return f"{number} {unit}"


def payment_method_label(value: Any) -> str:
    """Normaliza métodos de pago a etiquetas para pantalla."""
    normalized = clean_text(enum_value(value)).lower()
    labels = {
        "cash": "Efectivo",
        "bank_transfer": "Transferencia bancaria",
        "bank": "Transferencia bancaria",
        "card": "Tarjeta",
    }
    return labels.get(normalized, clean_text(value, "No especificado"))


def receipt_status_label(value: Any) -> str:
    """Normaliza estados de recibo a etiquetas para pantalla."""
    normalized = clean_text(enum_value(value)).lower()
    labels = {
        "paid": "Pagado",
        "pending": "Pendiente",
        "expired": "Vencido",
    }
    return labels.get(normalized, clean_text(value, "Sin estado"))


def grade_status_label(value: Any) -> str:
    """Normaliza estados académicos para tablas de notas."""
    normalized = clean_text(enum_value(value)).lower()

    if normalized in {"passed", "pass", "aprobado", "academicstatus.passed"}:
        return "Aprobado"
    if normalized in {"failed", "fail", "reprobado", "academicstatus.failed"}:
        return "Reprobado"

    return "Pendiente"


def format_grade(value: Any, empty: str = "—") -> str:
    """Formatea una nota con dos decimales."""
    if value in (None, ""):
        return empty
    return f"{read_float(value):.2f}"


def clear_layout(layout: Any) -> None:
    """Elimina widgets de un layout sin dejar referencias visuales colgantes."""
    if layout is None:
        return

    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()

        if widget is not None:
            widget.deleteLater()
        elif child_layout is not None:
            clear_layout(child_layout)


def calculate_card_columns(width: int) -> int:
    """Calcula columnas de tarjetas según el ancho disponible."""
    if width >= 980:
        return 3
    if width >= 650:
        return 2
    return 1
