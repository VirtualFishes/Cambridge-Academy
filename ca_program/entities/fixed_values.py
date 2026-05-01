from enum import Enum

class UserRole(Enum):
    ADMIN = "administrator"
    PROFESSOR = "professor"
    STUDENT = "student"

class AcademicStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"

class ReceiptStatus(Enum):
    PAID = "paid"
    EXPIRED = "expired"
    PENDING = "pending"

class PaymentMethod(Enum):
    CASH = "cash"
    BANK = "bank_transfer"
    CARD = "card"
