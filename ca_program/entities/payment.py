from datetime import date

from ca_program.entities.fixed_values import PaymentMethod
from ca_program.entities.receipt import Receipt


class Payment:
    def __init__(
        self,
        id_payment: int,
        payment_date: date,
        payment_method: PaymentMethod,
        receipt: Receipt,
    ):
        self.id_payment = id_payment
        self.payment_date = payment_date
        self.payment_method = payment_method
        self.receipt = receipt

    def __str__(self) -> str:
        return f"Pago {self.id_payment} - {self.payment_method.value}"
