"""
Valores fijos del dominio académico.

Las enumeraciones evitan cadenas mágicas dispersas por el sistema y mantienen
consistentes los estados, roles y métodos de pago usados por entidades, modelos,
servicios y vistas.
"""

from enum import Enum


class UserRole(Enum):
    """Roles autorizados para controlar el acceso al sistema."""

    ADMIN = "administrator"
    PROFESSOR = "professor"
    STUDENT = "student"


class AcademicStatus(Enum):
    """Estados académicos posibles para el resultado final de una matrícula."""

    PASSED = "passed"
    FAILED = "failed"


class ReceiptStatus(Enum):
    """Estados administrativos de un recibo de pago."""

    PAID = "paid"
    EXPIRED = "expired"
    PENDING = "pending"


class PaymentMethod(Enum):
    """Medios de pago aceptados por la academia."""

    CASH = "cash"
    BANK = "bank_transfer"
    CARD = "card"
