"""
Utilidades compartidas para las vistas del submódulo professor_view.

El objetivo de este archivo es concentrar operaciones repetidas de presentación:
lectura segura de diccionarios, formateo de valores, cálculo visual de notas y
limpieza de layouts. No consulta servicios, modelos ni base de datos.
"""

from __future__ import annotations

from typing import Any


def clean_text(value: Any, default: str = "") -> str:
    """Convierte un valor a texto visible sin exponer None ni cadenas vacías."""
    if value in (None, ""):
        return default

    text = str(value).strip()
    return text if text else default


def read_mapping_value(mapping: Any, *keys: str, default: str = "") -> str:
    """Lee el primer valor disponible dentro de un diccionario simple."""
    if not isinstance(mapping, dict):
        return default

    for key in keys:
        value = mapping.get(key)
        text = clean_text(value)
        if text:
            return text
    return default


def read_float(value: Any, default: float = 0.0) -> float:
    """Convierte un valor a float aceptando separador decimal con coma."""
    if isinstance(value, str):
        value = value.strip().replace(",", ".")

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_int(value: Any, default: int = 0) -> int:
    """Convierte un valor a entero de forma tolerante para datos de la GUI."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def calculate_average(*grades: Any) -> float:
    """Calcula el promedio simple de las notas recibidas."""
    numeric_grades = [read_float(grade) for grade in grades]
    if not numeric_grades:
        return 0.0
    return round(sum(numeric_grades) / len(numeric_grades), 2)


def status_label_from_average(average: Any, passing_grade: float = 3.0) -> str:
    """Retorna la etiqueta académica visible a partir de un promedio."""
    return "Aprobado" if read_float(average) >= passing_grade else "Reprobado"


def normalize_status_label(status: Any, default: str = "Sin estado") -> str:
    """Normaliza estados académicos internos a etiquetas comprensibles."""
    value = clean_text(status).lower()

    if value in {"passed", "pass", "aprobado", "academicstatus.passed"}:
        return "Aprobado"
    if value in {"failed", "fail", "reprobado", "academicstatus.failed"}:
        return "Reprobado"
    if value in {"pending", "pendiente"}:
        return "Pendiente"

    return clean_text(status, default).capitalize() if value else default


def format_grade(value: Any, empty: str = "0.00") -> str:
    """Formatea una nota o promedio con dos decimales."""
    if value in (None, ""):
        return empty
    return f"{read_float(value):.2f}"


def format_date(value: Any, default: str = "No registrada") -> str:
    """Formatea una fecha simple para presentación en pantalla."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return clean_text(value, default)


def format_price(value: Any, default: str = "No registrado") -> str:
    """Formatea un precio para las tarjetas de cursos del profesor."""
    amount = read_float(value, -1.0)
    if amount <= 0:
        return default
    return f"${amount:,.2f}"


def format_unit_count(value: Any, singular: str, plural: str, default: str = "No registrada") -> str:
    """Formatea cantidades con unidad en singular o plural."""
    number = read_float(value, -1.0)
    if number <= 0:
        return default

    visible_number: int | float = int(number) if number.is_integer() else number
    unit = singular if number == 1 else plural
    return f"{visible_number} {unit}"


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
