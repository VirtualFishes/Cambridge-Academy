"""
Utilidades compartidas para las vistas administrativas.

Este módulo concentra funciones pequeñas y reutilizables de presentación:
lectura segura de estructuras, formateo de fechas y valores monetarios, y
creación de elementos de tabla. No contiene reglas de negocio ni acceso a base
de datos; por tanto, conserva la responsabilidad de la capa View.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


def read_first(mapping: dict | None, *keys: str, default: Any = None) -> Any:
    """Retorna el primer valor no vacío encontrado en un diccionario."""
    if not isinstance(mapping, dict):
        return default

    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return default


def enum_value(value: Any) -> Any:
    """Extrae el valor real de un Enum o retorna el valor original."""
    return getattr(value, "value", value)


def safe_text(value: Any, default: str = "—") -> str:
    """Convierte un valor a texto visible y evita mostrar None o cadenas vacías."""
    if value is None or value == "":
        return default
    return str(value)


def get_nested_value(source: Any, path: str, default: Any = None) -> Any:
    """Lee valores anidados desde dicts, objetos o rutas alternativas con '|'."""
    if not path:
        return default

    if "|" in path:
        for option in path.split("|"):
            value = get_nested_value(source, option.strip(), default=default)
            if value not in (None, ""):
                return value
        return default

    current = source
    for part in path.split("."):
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, (list, tuple)):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return default
        else:
            current = getattr(current, part, default)
    return current if current is not None else default


def build_search_blob(record: Any, fields: Iterable[str]) -> str:
    """Construye una cadena normalizada para búsquedas simples en tablas."""
    values = [safe_text(get_nested_value(record, field), "") for field in fields]
    return " ".join(values).lower().strip()


def format_date(value: Any) -> str:
    """Formatea fechas en YYYY-MM-DD sin fallar ante valores no fecha."""
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def format_currency(value: Any) -> str:
    """Formatea valores monetarios al estilo usado en la interfaz administrativa."""
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"$ {amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def make_table_item(value: Any, alignment: Qt.AlignmentFlag | Qt.Alignment = Qt.AlignVCenter | Qt.AlignLeft) -> QTableWidgetItem:
    """Crea un QTableWidgetItem con texto seguro y alineación uniforme."""
    item = QTableWidgetItem(safe_text(value))
    item.setTextAlignment(alignment)
    return item


def configure_table_columns(table: QTableWidget, columns: list[tuple], resize_mode=QHeaderView.Interactive) -> None:
    """Configura anchos de columnas de manera consistente en tablas administrativas."""
    header = table.horizontalHeader()
    header.setSectionResizeMode(resize_mode)
    header.setStretchLastSection(False)
    for index, column in enumerate(columns):
        if len(column) >= 3:
            table.setColumnWidth(index, int(column[2]))


def user_display_name(user: Any, default: str = "Usuario") -> str:
    """Obtiene un nombre legible desde una entidad User o un diccionario."""
    if isinstance(user, dict):
        return safe_text(read_first(user, "name", "username", default=default), default)
    return safe_text(getattr(user, "name", default), default)
