"""
Entidad Receipt.

Representa un recibo generado por la matrícula de un estudiante en un curso. La
entidad valida coherencia básica de fechas, valor y estado administrativo.
"""

from dataclasses import dataclass
from datetime import date

from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import ReceiptStatus
from ca_program.entities._validators import (
    require_date_order,
    require_enum_member,
    require_instance,
    require_positive_integer,
    require_positive_number,
)


@dataclass
class Receipt:
    """Documento de cobro asociado a una matrícula."""

    id_receipt: int
    issue_date: date
    due_date: date
    amount: float
    status: ReceiptStatus
    enrollment: Enrollment

    def __post_init__(self) -> None:
        """Valida que el recibo tenga datos administrativos consistentes."""
        require_positive_integer(self.id_receipt, "id_receipt")
        require_date_order(self.issue_date, self.due_date, "issue_date", "due_date")
        require_positive_number(self.amount, "amount")
        require_enum_member(self.status, ReceiptStatus, "status")
        require_instance(self.enrollment, Enrollment, "enrollment")

    def __str__(self) -> str:
        """Retorna una descripción legible del recibo."""
        return f"Recibo {self.id_receipt} - {self.status.value}"
