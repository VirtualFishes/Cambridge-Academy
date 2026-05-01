"""
Utilidades internas compartidas por la capa ``models``.

Este módulo concentra validaciones y pequeños mapeos repetidos para mantener
los modelos simples, consistentes y alineados con DRY. No contiene reglas de
negocio de servicios ni lógica de interfaz; solo apoyo técnico para
persistencia, normalización de datos y construcción de entidades.
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import TypeVar

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.user import User

TEnum = TypeVar("TEnum", bound=Enum)
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def require_text(value: object, field_name: str) -> str:
    """
    Retorna un texto limpio y valida que no esté vacío.

    Los modelos reciben datos desde servicios y vistas. Esta función evita
    insertar cadenas vacías o valores nulos en campos obligatorios.
    """
    if value is None:
        raise ValueError(f"{field_name} es obligatorio.")

    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} es obligatorio.")

    return text


def optional_text(value: object) -> str | None:
    """Retorna texto limpio o None cuando el valor no fue suministrado."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def require_identifier(value: object, field_name: str) -> str:
    """Valida identificadores de dominio como cédulas o códigos de curso."""
    return require_text(value, field_name)


def require_positive_int(value: object, field_name: str) -> int:
    """Valida números enteros positivos usados como identificadores o duraciones."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} debe ser un número entero.")

    if number <= 0:
        raise ValueError(f"{field_name} debe ser mayor que cero.")

    return number


def require_positive_number(value: object, field_name: str) -> float:
    """Valida importes o valores numéricos que deben ser mayores que cero."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} debe ser un número válido.")

    if number <= 0:
        raise ValueError(f"{field_name} debe ser mayor que cero.")

    return number


def require_non_negative_number(value: object, field_name: str) -> float:
    """Valida valores numéricos que pueden ser cero, pero no negativos."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} debe ser un número válido.")

    if number < 0:
        raise ValueError(f"{field_name} no puede ser negativo.")

    return number


def require_grade_value(value: object, field_name: str) -> float:
    """Valida una nota académica dentro de la escala institucional 0.0 a 5.0."""
    number = require_non_negative_number(value, field_name)
    if number > 5.0:
        raise ValueError(f"{field_name} debe estar entre 0.0 y 5.0.")

    return number


def require_date(value: object, field_name: str):
    """Valida presencia de fechas sin acoplar el modelo a un widget específico."""
    if value is None:
        raise ValueError(f"{field_name} es obligatorio.")

    return value


def require_date_order(start_value: object, end_value: object, start_field: str, end_field: str) -> None:
    """Valida que una fecha final no sea anterior a su fecha inicial."""
    start = require_date(start_value, start_field)
    end = require_date(end_value, end_field)

    if isinstance(start, date) and isinstance(end, date) and end < start:
        raise ValueError(f"{end_field} no puede ser anterior a {start_field}.")


def validate_email(email: object) -> str:
    """Normaliza y valida correos electrónicos de usuarios del sistema."""
    clean_email = require_text(email, "Correo electrónico")

    if not _EMAIL_PATTERN.match(clean_email):
        raise ValueError("El correo electrónico no tiene un formato válido.")

    return clean_email.lower()


def normalize_enum(value: object, enum_type: type[TEnum], field_name: str) -> TEnum:
    """
    Convierte cadenas o miembros Enum al Enum esperado.

    Acepta tanto el valor almacenado en base de datos como el nombre del miembro
    para tolerar entradas controladas provenientes de servicios o pruebas.
    """
    if isinstance(value, enum_type):
        return value

    clean_value = require_text(value, field_name)

    try:
        return enum_type(clean_value)
    except ValueError:
        try:
            return enum_type[clean_value.upper()]
        except KeyError:
            valid_values = ", ".join(member.value for member in enum_type)
            raise ValueError(f"{field_name} no es válido. Valores permitidos: {valid_values}.")


def build_user_entity(
    id_user: int,
    name: str,
    password: str,
    role: str | UserRole,
    email: str,
    birth_date,
    nationality: str,
) -> User:
    """Construye una entidad User desde columnas de base de datos."""
    return User(
        id_user=id_user,
        name=name,
        password=password,
        role=normalize_enum(role, UserRole, "Rol"),
        email=email,
        birth_date=birth_date,
        nationality=nationality,
    )
