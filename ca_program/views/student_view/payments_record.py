from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PaymentsRecordWidget(QWidget):
    """Vista de historial de pagos para usuarios con rol estudiante.

    HU-22: permite consultar los pagos realizados por el estudiante.

    La vista se concentra en presentar la información. Para mantenerla flexible
    con la arquitectura MVC + Entities, puede recibir un proveedor externo de
    datos mediante set_payment_history_provider(...). Mientras se integra ese
    servicio, incluye una consulta de respaldo usando PaymentModel, que ya fue
    preparado en HU-21 para consultar pagos por usuario estudiante.
    """

    def __init__(
        self,
        user=None,
        payment_history_provider: Callable[[object], dict] | None = None,
    ):
        super().__init__()
        self.user = user
        self.payment_history_provider = payment_history_provider
        self.payments: list[dict] = []

        self._build_ui()
        self.load_payments()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("studentHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("Historial de pagos")
        title.setObjectName("studentPageTitle")

        subtitle = QLabel(
            "Consulta los pagos realizados y verifica los datos asociados a tus cursos."
        )
        subtitle.setObjectName("studentPageSubtitle")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.load_payments)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(refresh_button, 0, Qt.AlignTop)

        self.summary_panel = QFrame()
        self.summary_panel.setObjectName("paymentsSummaryPanel")
        summary_layout = QHBoxLayout(self.summary_panel)
        summary_layout.setContentsMargins(18, 16, 18, 16)
        summary_layout.setSpacing(14)

        self.total_paid_card = self._create_summary_card("Total pagado", "$ 0")
        self.payment_count_card = self._create_summary_card("Pagos realizados", "0")
        self.last_payment_card = self._create_summary_card("Último pago", "Sin registros")

        summary_layout.addWidget(self.total_paid_card, 1)
        summary_layout.addWidget(self.payment_count_card, 1)
        summary_layout.addWidget(self.last_payment_card, 1)

        self.records_panel = QFrame()
        self.records_panel.setObjectName("paymentsPanel")
        records_panel_layout = QVBoxLayout(self.records_panel)
        records_panel_layout.setContentsMargins(0, 0, 0, 0)
        records_panel_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("paymentsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("paymentsScrollContent")
        self.scroll_content.setMinimumHeight(360)

        self.records_layout = QVBoxLayout(self.scroll_content)
        self.records_layout.setContentsMargins(22, 22, 22, 22)
        self.records_layout.setSpacing(14)
        self.records_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        records_panel_layout.addWidget(self.scroll_area)

        main_layout.addWidget(header)
        main_layout.addWidget(self.summary_panel)
        main_layout.addWidget(self.records_panel, 1)

    def set_user(self, user):
        """Actualiza el usuario estudiante usado para consultar pagos."""
        self.user = user
        self.load_payments()

    def set_payment_history_provider(
        self,
        provider: Callable[[object], dict] | None,
    ):
        """Define el proveedor de datos del historial de pagos."""
        self.payment_history_provider = provider
        self.load_payments()

    def load_payments(self):
        id_user = self._get_user_id()

        if not id_user:
            self.payments = []
            self._render_payments("No fue posible identificar al estudiante autenticado.")
            return

        result = self._get_payment_history(id_user)

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible consultar los pagos",
                result.get("message", "Ocurrió un error al consultar el historial de pagos."),
            )
            self.payments = []
            self._render_payments("No fue posible cargar el historial de pagos.")
            return

        payments = result.get("payments") or result.get("data") or []
        self.payments = [self._normalize_payment(payment) for payment in payments]
        self._render_payments()

    def _get_payment_history(self, id_user) -> dict:
        if callable(self.payment_history_provider):
            return self.payment_history_provider(id_user)

        try:
            from ca_program.models.payment_model import PaymentModel
        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "No hay un proveedor disponible para consultar el historial de pagos.",
                "payments": [],
                "data": [],
            }

        try:
            payment_entities = PaymentModel.get_payments_by_student_user_id(id_user)
            payment_records = [self._payment_entity_to_dict(payment) for payment in payment_entities]
            return {
                "success": True,
                "message": "Historial de pagos consultado correctamente.",
                "payments": payment_records,
                "entities": payment_entities,
                "data": payment_records,
            }
        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al consultar el historial de pagos.",
                "payments": [],
                "data": [],
            }

    def _render_payments(self, empty_message: str | None = None):
        self._clear_records()
        self._update_summary()

        if not self.payments:
            message = empty_message or "Aún no tienes pagos registrados."
            empty_state = self._create_empty_state(message)
            self.records_layout.addWidget(empty_state, 1)
            return

        for payment in self.payments:
            self.records_layout.addWidget(self._create_payment_card(payment))

        self.records_layout.addStretch(1)

    def _create_summary_card(self, label_text: str, value_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("paymentSummaryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("paymentSummaryLabel")

        value = QLabel(value_text)
        value.setObjectName("paymentSummaryValue")
        value.setWordWrap(True)

        layout.addWidget(label)
        layout.addWidget(value)
        card.value_label = value
        return card

    def _create_payment_card(self, payment: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("paymentRecordCard")
        card.setMinimumHeight(150)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        title_box = QWidget()
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        course_name = QLabel(payment.get("course_name") or "Curso no identificado")
        course_name.setObjectName("paymentCourseTitle")
        course_name.setWordWrap(True)

        receipt_label = QLabel(
            f"Recibo #{self._safe_text(payment.get('id_receipt'))} · Pago #{self._safe_text(payment.get('id_payment'))}"
        )
        receipt_label.setObjectName("paymentReceiptLabel")

        title_layout.addWidget(course_name)
        title_layout.addWidget(receipt_label)

        amount_badge = QLabel(self._format_currency(payment.get("amount")))
        amount_badge.setObjectName("paymentAmountBadge")
        amount_badge.setAlignment(Qt.AlignCenter)
        amount_badge.setMinimumWidth(110)

        top_layout.addWidget(title_box, 1)
        top_layout.addWidget(amount_badge, 0, Qt.AlignTop)

        details_layout = QHBoxLayout()
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)

        details_layout.addWidget(
            self._create_detail_item("Fecha de pago", self._format_date(payment.get("payment_date"))),
            1,
        )
        details_layout.addWidget(
            self._create_detail_item("Método", self._format_payment_method(payment.get("payment_method"))),
            1,
        )
        details_layout.addWidget(
            self._create_detail_item("Estado", self._format_receipt_status(payment.get("receipt_status"))),
            1,
        )
        details_layout.addWidget(
            self._create_detail_item("Fecha límite original", self._format_date(payment.get("due_date"))),
            1,
        )

        professor = payment.get("professor_name") or "Sin profesor asignado"
        course_code = self._safe_text(payment.get("code_course"))
        footer = QLabel(f"Curso: {course_code} · Profesor: {professor}")
        footer.setObjectName("paymentFooterLabel")
        footer.setWordWrap(True)

        layout.addLayout(top_layout)
        layout.addLayout(details_layout)
        layout.addWidget(footer)

        return card

    def _create_detail_item(self, label_text: str, value_text: str) -> QFrame:
        item = QFrame()
        item.setObjectName("paymentDetailItem")
        layout = QVBoxLayout(item)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("paymentDetailLabel")

        value = QLabel(value_text)
        value.setObjectName("paymentDetailValue")
        value.setWordWrap(True)

        layout.addWidget(label)
        layout.addWidget(value)
        return item

    def _create_empty_state(self, message: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("paymentEmptyState")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Sin pagos registrados")
        title.setObjectName("paymentEmptyTitle")
        title.setAlignment(Qt.AlignCenter)

        detail = QLabel(message)
        detail.setObjectName("paymentEmptyDetail")
        detail.setAlignment(Qt.AlignCenter)
        detail.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(detail)
        return frame

    def _update_summary(self):
        total_paid = sum(float(payment.get("amount") or 0) for payment in self.payments)
        payment_count = len(self.payments)
        last_payment = self._format_date(self.payments[0].get("payment_date")) if self.payments else "Sin registros"

        self.total_paid_card.value_label.setText(self._format_currency(total_paid))
        self.payment_count_card.value_label.setText(str(payment_count))
        self.last_payment_card.value_label.setText(last_payment)

    def _clear_records(self):
        while self.records_layout.count():
            item = self.records_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _normalize_payment(self, payment) -> dict:
        if isinstance(payment, dict):
            receipt = payment.get("receipt") or {}
            enrollment = receipt.get("enrollment") or {}
            course = enrollment.get("course") or payment.get("course") or {}
            professor = course.get("professor") or {}

            return {
                "id_payment": payment.get("id_payment"),
                "payment_date": payment.get("payment_date"),
                "payment_method": payment.get("payment_method"),
                "id_receipt": receipt.get("id_receipt") or payment.get("id_receipt"),
                "amount": receipt.get("amount") or payment.get("amount"),
                "receipt_status": receipt.get("status") or payment.get("receipt_status"),
                "issue_date": receipt.get("issue_date") or payment.get("issue_date"),
                "due_date": receipt.get("due_date") or payment.get("due_date"),
                "code_course": course.get("code_course") or payment.get("code_course"),
                "course_name": course.get("name") or payment.get("course_name"),
                "professor_name": professor.get("name") or payment.get("professor_name"),
            }

        return self._payment_entity_to_dict(payment)

    def _payment_entity_to_dict(self, payment) -> dict:
        receipt = getattr(payment, "receipt", None)
        enrollment = getattr(receipt, "enrollment", None)
        course = getattr(enrollment, "course", None)
        professor = getattr(course, "professor", None)
        professor_user = getattr(professor, "user", None)
        payment_method = getattr(payment, "payment_method", "")
        receipt_status = getattr(receipt, "status", "")

        return {
            "id_payment": getattr(payment, "id_payment", ""),
            "payment_date": getattr(payment, "payment_date", ""),
            "payment_method": getattr(payment_method, "value", payment_method),
            "id_receipt": getattr(receipt, "id_receipt", ""),
            "amount": getattr(receipt, "amount", 0),
            "receipt_status": getattr(receipt_status, "value", receipt_status),
            "issue_date": getattr(receipt, "issue_date", ""),
            "due_date": getattr(receipt, "due_date", ""),
            "code_course": getattr(course, "code_course", ""),
            "course_name": getattr(course, "name", ""),
            "professor_name": getattr(professor_user, "name", ""),
        }

    def _get_user_id(self):
        return getattr(self.user, "id_user", None)

    @staticmethod
    def _format_currency(value) -> str:
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0

        if amount.is_integer():
            return f"$ {int(amount)}"
        return f"$ {amount:,.2f}"

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "Sin fecha"

        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y")

        return str(value)

    @staticmethod
    def _format_payment_method(value) -> str:
        value = str(value or "").strip()
        labels = {
            "cash": "Efectivo",
            "bank_transfer": "Transferencia bancaria",
            "card": "Tarjeta",
        }
        return labels.get(value, value or "No especificado")

    @staticmethod
    def _format_receipt_status(value) -> str:
        value = str(value or "").strip()
        labels = {
            "paid": "Pagado",
            "pending": "Pendiente",
            "expired": "Vencido",
        }
        return labels.get(value, value or "Sin estado")

    @staticmethod
    def _safe_text(value) -> str:
        if value is None or value == "":
            return "—"
        return str(value)
