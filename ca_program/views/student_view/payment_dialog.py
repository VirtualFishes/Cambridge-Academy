from datetime import date, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ca_program.entities.fixed_values import PaymentMethod


class PaymentDialog(QDialog):
    """Diálogo simple para confirmar el pago simulado de un recibo.

    Este componente pertenece a la capa Views. No registra pagos ni modifica
    recibos; únicamente presenta la información del recibo pendiente y retorna
    el método de pago seleccionado para que StudentGUI delegue el proceso al
    servicio correspondiente.
    """

    PAYMENT_OPTIONS = (
        ("Efectivo", PaymentMethod.CASH),
        ("Transferencia bancaria", PaymentMethod.BANK),
        ("Tarjeta", PaymentMethod.CARD),
    )

    def __init__(self, course: dict | None = None, receipt: dict | object | None = None, parent=None):
        super().__init__(parent)
        self.course = course or {}
        self.receipt = receipt or {}

        self.setWindowTitle("Pagar recibo")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setObjectName("paymentDialog")
        self.setStyleSheet(self.get_styles())

        self.method_combo: QComboBox | None = None
        self.confirm_button: QPushButton | None = None
        self.cancel_button: QPushButton | None = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(18)

        title = QLabel("Confirmar pago")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignLeft)

        subtitle = QLabel(
            "Selecciona un método de pago para completar la inscripción del curso."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)

        receipt_panel = QFrame()
        receipt_panel.setObjectName("receiptPanel")
        receipt_layout = QVBoxLayout(receipt_panel)
        receipt_layout.setContentsMargins(18, 16, 18, 16)
        receipt_layout.setSpacing(12)

        receipt_layout.addLayout(
            self._create_info_row("Curso", self._get_course_name())
        )
        receipt_layout.addLayout(
            self._create_info_row("Valor a pagar", self._format_price(self._get_receipt_amount()))
        )
        receipt_layout.addLayout(
            self._create_info_row("Fecha límite", self._format_date(self._get_receipt_value("due_date")))
        )
        receipt_layout.addLayout(
            self._create_info_row("Estado", self._format_status(self._get_receipt_value("status")))
        )

        method_label = QLabel("Método de pago")
        method_label.setObjectName("fieldLabel")

        self.method_combo = QComboBox()
        self.method_combo.setObjectName("methodCombo")
        for label, method in self.PAYMENT_OPTIONS:
            self.method_combo.addItem(label, method)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)

        self.confirm_button = QPushButton("Confirmar pago")
        self.confirm_button.setObjectName("primaryButton")
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.confirm_button)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(receipt_panel)
        main_layout.addWidget(method_label)
        main_layout.addWidget(self.method_combo)
        main_layout.addLayout(button_layout)

    def selected_payment_method(self) -> PaymentMethod:
        """Retorna el método de pago seleccionado como PaymentMethod."""
        if self.method_combo is None:
            return PaymentMethod.CASH

        method = self.method_combo.currentData()
        if isinstance(method, PaymentMethod):
            return method

        return PaymentMethod.CASH

    def selected_payment_method_value(self) -> str:
        """Retorna el valor persistible del método de pago seleccionado."""
        return self.selected_payment_method().value

    def _create_info_row(self, label: str, value: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        label_widget = QLabel(label)
        label_widget.setObjectName("infoLabel")
        label_widget.setMinimumWidth(125)

        value_widget = QLabel(value)
        value_widget.setObjectName("infoValue")
        value_widget.setWordWrap(True)
        value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row.addWidget(label_widget)
        row.addWidget(value_widget, 1)
        return row

    def _get_course_name(self) -> str:
        name = str(self.course.get("name", "")).strip()
        return name or "Curso seleccionado"

    def _get_receipt_amount(self):
        amount = self._get_receipt_value("amount")
        if amount in (None, ""):
            amount = self.course.get("price")
        return amount

    def _get_receipt_value(self, key: str):
        if isinstance(self.receipt, dict):
            return self.receipt.get(key)

        if hasattr(self.receipt, key):
            return getattr(self.receipt, key)

        return None

    def _format_price(self, price) -> str:
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            return "No registrado"

        if numeric_price <= 0:
            return "No registrado"

        formatted = f"{numeric_price:,.0f}".replace(",", ".")
        return f"$ {formatted}"

    def _format_date(self, value) -> str:
        if value in (None, ""):
            return "No registrada"

        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y")

        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")

        text = str(value).strip()
        if not text:
            return "No registrada"

        for date_format in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text[:19], date_format)
                return parsed.strftime("%d/%m/%Y")
            except ValueError:
                continue

        return text

    def _format_status(self, status) -> str:
        raw_status = getattr(status, "value", status)
        normalized = str(raw_status or "").strip().lower()

        labels = {
            "pending": "Pendiente de pago",
            "paid": "Pagado",
            "expired": "Vencido",
        }
        return labels.get(normalized, "Pendiente de pago")

    def get_styles(self) -> str:
        return """
        QDialog#paymentDialog {
            background-color: #e1e7f0;
            color: #1e293b;
            font-size: 14px;
        }

        QLabel#dialogTitle {
            color: #1e3a8a;
            font-size: 22px;
            font-weight: bold;
        }

        QLabel#dialogSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QFrame#receiptPanel {
            background-color: #ffffff;
            border: 1px solid #dbe4f0;
            border-radius: 14px;
        }

        QLabel#infoLabel,
        QLabel#fieldLabel {
            color: #64748b;
            font-weight: bold;
        }

        QLabel#infoValue {
            color: #0f172a;
            font-weight: bold;
        }

        QComboBox#methodCombo {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 10px;
            min-height: 22px;
        }

        QComboBox#methodCombo:focus {
            border: 1px solid #2563eb;
        }

        QComboBox#methodCombo QAbstractItemView {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            selection-background-color: #2563eb;
            selection-color: #ffffff;
            outline: 0;
            padding: 4px;
        }

        QComboBox#methodCombo::drop-down {
            border: none;
            width: 28px;
        }

        QComboBox#methodCombo::down-arrow {
            width: 10px;
            height: 10px;
        }

        QPushButton {
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: bold;
        }

        QPushButton#primaryButton {
            background-color: #16a34a;
            color: white;
        }

        QPushButton#primaryButton:hover {
            background-color: #15803d;
        }

        QPushButton#secondaryButton {
            background-color: #e2e8f0;
            color: #1e293b;
        }

        QPushButton#secondaryButton:hover {
            background-color: #cbd5e1;
        }
        """
