"""
Entidad Payment.

Representa el pago realizado sobre un recibo. Su alcance se limita a los datos
propios del pago y a la asociación con el recibo correspondiente.
"""

from dataclasses import dataclass
from datetime import date

from ca_program.entities.fixed_values import PaymentMethod
from ca_program.entities.receipt import Receipt
from ca_program.entities._validators import (
    require_date,
    require_enum_member,
    require_instance,
    require_positive_integer,
)


@dataclass
class Payment:
    """Pago registrado para un recibo académico."""

    id_payment: int
    payment_date: date
    payment_method: PaymentMethod
    receipt: Receipt

    def __post_init__(self) -> None:
        """Valida identificador, fecha, método de pago y recibo asociado."""
        require_positive_integer(self.id_payment, "id_payment")
        require_date(self.payment_date, "payment_date")
        require_enum_member(self.payment_method, PaymentMethod, "payment_method")
        require_instance(self.receipt, Receipt, "receipt")

    def __str__(self) -> str:
        """Retorna una descripción legible del pago."""
        return f"Pago {self.id_payment} - {self.payment_method.value}"
