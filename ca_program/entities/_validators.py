"""
Utilidades internas de validación para las entidades del dominio.

Este módulo concentra reglas estructurales simples para evitar duplicación entre
entidades. No contiene lógica de base de datos, reglas de interfaz ni procesos de
servicio; únicamente protege invariantes mínimos de objetos del dominio.
"""

from datetime import date
from enum import Enum
from numbers import Real
from typing import TypeVar

T = TypeVar("T")


def require_instance(value: object, expected_type: type[T], field_name: str) -> None:
    """Valida que un atributo sea instancia del tipo esperado."""
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} debe ser de tipo {expected_type.__name__}.")


def require_enum_member(value: object, enum_type: type[Enum], field_name: str) -> None:
    """Valida que un atributo corresponda a un miembro de una enumeración."""
    if not isinstance(value, enum_type):
        raise TypeError(f"{field_name} debe ser un valor de {enum_type.__name__}.")


def require_non_empty_string(value: object, field_name: str) -> None:
    """Valida que un atributo textual exista y no esté vacío."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} debe ser una cadena de texto.")
    if not value.strip():
        raise ValueError(f"{field_name} no puede estar vacío.")


def require_positive_integer(value: object, field_name: str) -> None:
    """Valida identificadores y cantidades enteras positivas."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} debe ser un número entero.")
    if value <= 0:
        raise ValueError(f"{field_name} debe ser mayor que cero.")


def require_positive_number(value: object, field_name: str) -> None:
    """Valida importes, precios u otros valores numéricos positivos."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} debe ser un número.")
    if value <= 0:
        raise ValueError(f"{field_name} debe ser mayor que cero.")


def require_number_in_range(
    value: object,
    field_name: str,
    minimum: float,
    maximum: float,
) -> None:
    """Valida que un valor numérico se mantenga dentro de un rango permitido."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} debe ser un número.")
    if not minimum <= float(value) <= maximum:
        raise ValueError(f"{field_name} debe estar entre {minimum} y {maximum}.")


def require_date(value: object, field_name: str) -> None:
    """Valida que un atributo sea una fecha del calendario."""
    if not isinstance(value, date):
        raise TypeError(f"{field_name} debe ser una fecha válida.")


def require_date_order(
    start_date: date,
    end_date: date,
    start_field: str,
    end_field: str,
) -> None:
    """Valida que una fecha final no sea anterior a su fecha inicial."""
    require_date(start_date, start_field)
    require_date(end_date, end_field)
    if end_date < start_date:
        raise ValueError(f"{end_field} no puede ser anterior a {start_field}.")
