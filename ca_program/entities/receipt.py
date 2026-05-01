from datetime import date

from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import ReceiptStatus


class Receipt:
    def __init__(
        self,
        id_receipt: int,
        issue_date: date,
        due_date: date,
        amount: float,
        status: ReceiptStatus,
        enrollment: Enrollment,
    ):
        self.id_receipt = id_receipt
        self.issue_date = issue_date
        self.due_date = due_date
        self.amount = amount
        self.status = status
        self.enrollment = enrollment

    def __str__(self) -> str:
        return f"Recibo {self.id_receipt} - {self.status.value}"
