"""Vista administrativa para consulta de pagos.

La pantalla presenta información financiera de solo lectura. Siempre intenta
consumir un servicio de pagos si existe y mantiene una ruta de compatibilidad
para proyectos donde ese servicio aún no se haya creado.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ca_program.views.admin_view.admin_view_utils import (
    configure_table_columns,
    enum_value,
    format_currency,
    format_date,
    make_table_item,
    safe_text,
)


class PaymentsGUI(QWidget):
    """Vista administrativa para consultar pagos de estudiantes.

    HU-16: permite al usuario administrativo revisar el historial general de
    pagos registrados en el sistema para control financiero.

    Esta vista no modifica pagos, recibos ni inscripciones. Solo consulta y
    presenta información financiera consolidada.
    """

    METHOD_LABELS = {
        "cash": "Efectivo",
        "bank_transfer": "Transferencia bancaria",
        "card": "Tarjeta",
    }

    STATUS_LABELS = {
        "paid": "Pagado",
        "pending": "Pendiente",
        "expired": "Vencido",
    }

    COLUMNS = [
        ("Pago", "id_payment", 80),
        ("Fecha de pago", "payment_date", 130),
        ("Estudiante", "student_name", 180),
        ("Documento", "id_student", 125),
        ("Curso", "course_name", 180),
        ("Profesor", "professor_name", 170),
        ("Recibo", "id_receipt", 90),
        ("Valor", "amount", 110),
        ("Método", "payment_method", 170),
        ("Estado recibo", "receipt_status", 125),
        ("Emitido", "issue_date", 115),
        ("Vence", "due_date", 115),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.payments: list[dict] = []
        self.filtered_payments: list[dict] = []

        self.setStyleSheet(self._get_local_styles())
        self._build_ui()
        self.load_payments()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        header = QFrame()
        header.setObjectName("paymentsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        title_box = QWidget()
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("Consulta de pagos")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Revisa los pagos realizados por los estudiantes y verifica el control financiero de las inscripciones."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.load_payments)

        header_layout.addWidget(title_box, 1)
        header_layout.addWidget(refresh_button, 0, Qt.AlignTop)

        self.summary_grid = QGridLayout()
        self.summary_grid.setSpacing(14)

        self.total_paid_card = self._create_summary_card("Total recaudado", "$ 0")
        self.payment_count_card = self._create_summary_card("Pagos registrados", "0")
        self.last_payment_card = self._create_summary_card("Último pago", "Sin registros")
        self.methods_card = self._create_summary_card("Métodos usados", "Sin registros")

        self.summary_grid.addWidget(self.total_paid_card, 0, 0)
        self.summary_grid.addWidget(self.payment_count_card, 0, 1)
        self.summary_grid.addWidget(self.last_payment_card, 0, 2)
        self.summary_grid.addWidget(self.methods_card, 0, 3)

        filters_panel = QFrame()
        filters_panel.setObjectName("paymentsFilterPanel")
        filters_layout = QHBoxLayout(filters_panel)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("paymentsSearchInput")
        self.search_input.setPlaceholderText("Buscar por estudiante, documento, curso, profesor, recibo o pago...")
        self.search_input.textChanged.connect(self.apply_filters)

        self.method_filter = QComboBox()
        self.method_filter.setObjectName("paymentsMethodFilter")
        self.method_filter.addItem("Todos los métodos", "")
        self.method_filter.addItem("Efectivo", "cash")
        self.method_filter.addItem("Transferencia bancaria", "bank_transfer")
        self.method_filter.addItem("Tarjeta", "card")
        self.method_filter.currentIndexChanged.connect(self.apply_filters)

        clear_button = QPushButton("Limpiar")
        clear_button.setObjectName("secondaryButton")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.clear_filters)

        filters_layout.addWidget(self.search_input, 1)
        filters_layout.addWidget(self.method_filter, 0)
        filters_layout.addWidget(clear_button, 0)

        table_panel = QFrame()
        table_panel.setObjectName("paymentsTablePanel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)

        table_header = QHBoxLayout()
        table_header.setContentsMargins(0, 0, 0, 0)
        table_header.setSpacing(10)

        table_title = QLabel("Pagos realizados")
        table_title.setObjectName("paymentsSectionTitle")

        self.counter_label = QLabel("0 registros")
        self.counter_label.setObjectName("paymentsCounterLabel")
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        table_header.addWidget(table_title, 1)
        table_header.addWidget(self.counter_label, 0)

        self.table = QTableWidget()
        self.table.setObjectName("paymentsTable")
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([column[0] for column in self.COLUMNS])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        configure_table_columns(self.table, self.COLUMNS, QHeaderView.Interactive)

        table_layout.addLayout(table_header)
        table_layout.addWidget(self.table, 1)

        root.addWidget(header)
        root.addLayout(self.summary_grid)
        root.addWidget(filters_panel)
        root.addWidget(table_panel, 1)

    def load_payments(self):
        """Carga pagos mediante servicio cuando existe y actualiza tabla/resumen."""
        try:
            payments, summary = self._fetch_payment_data()
            self.payments = payments
            self._update_summary(summary)
            self.apply_filters()
        except Exception as exc:
            print(exc)
            QMessageBox.warning(
                self,
                "No fue posible consultar los pagos",
                "Ocurrió un error al consultar los pagos realizados por los estudiantes.",
            )
            self.payments = []
            self.filtered_payments = []
            self._update_summary(self._empty_summary())
            self._render_table([])

    def _fetch_payment_data(self) -> tuple[list[dict], dict]:
        """Obtiene pagos desde PaymentService si está disponible.

        El fallback a PaymentModel conserva compatibilidad con versiones del
        proyecto que aún no tengan un servicio de pagos formalizado.
        """
        service_data = self._try_fetch_payments_from_service()
        if service_data is not None:
            return service_data

        from ca_program.models.payment_model import PaymentModel

        payment_entities = PaymentModel.get_all_payments()
        payments = [self._payment_entity_to_dict(payment) for payment in payment_entities]

        try:
            summary = PaymentModel.get_admin_payment_summary()
        except Exception as summary_error:
            print(summary_error)
            summary = self._calculate_summary(payments)

        return payments, summary

    def _try_fetch_payments_from_service(self) -> tuple[list[dict], dict] | None:
        """Intenta consumir un servicio de pagos sin acoplar la vista a su existencia."""
        try:
            from ca_program.services.payment_service import PaymentService
        except Exception:
            return None

        for method_name in ("get_admin_payments", "get_payments", "list_payments"):
            method = getattr(PaymentService, method_name, None)
            if not callable(method):
                continue

            result = method()
            if isinstance(result, dict) and result.get("success") is False:
                raise RuntimeError(result.get("message") or "No fue posible consultar los pagos.")

            if isinstance(result, dict):
                raw_payments = result.get("payments") or result.get("data") or []
                payments = [self._normalize_payment_record(payment) for payment in raw_payments]
                summary = result.get("summary") or self._calculate_summary(payments)
                return payments, summary

            if isinstance(result, list):
                payments = [self._normalize_payment_record(payment) for payment in result]
                return payments, self._calculate_summary(payments)

        return None

    def apply_filters(self):
        search_text = self.search_input.text().strip().lower()
        method_value = self.method_filter.currentData() or ""

        filtered = []
        for payment in self.payments:
            if method_value and payment.get("payment_method_value") != method_value:
                continue

            if search_text and not self._matches_search(payment, search_text):
                continue

            filtered.append(payment)

        self.filtered_payments = filtered
        self._render_table(filtered)

    def clear_filters(self):
        self.search_input.clear()
        self.method_filter.setCurrentIndex(0)
        self.apply_filters()

    def _render_table(self, payments: list[dict]):
        self.table.setRowCount(0)
        self.counter_label.setText(f"{len(payments)} registro{'s' if len(payments) != 1 else ''}")

        if not payments:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem("No hay pagos para mostrar.")
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.table.setSpan(0, 0, 1, len(self.COLUMNS))
            self.table.setItem(0, 0, empty_item)
            return

        self.table.setRowCount(len(payments))
        for row_index, payment in enumerate(payments):
            values = {
                "id_payment": self._safe_text(payment.get("id_payment")),
                "payment_date": self._format_date(payment.get("payment_date")),
                "student_name": self._safe_text(payment.get("student_name")),
                "id_student": self._safe_text(payment.get("id_student")),
                "course_name": self._safe_text(payment.get("course_name")),
                "professor_name": self._safe_text(payment.get("professor_name")),
                "id_receipt": self._safe_text(payment.get("id_receipt")),
                "amount": self._format_currency(payment.get("amount")),
                "payment_method": self._format_payment_method(payment.get("payment_method_value")),
                "receipt_status": self._format_receipt_status(payment.get("receipt_status_value")),
                "issue_date": self._format_date(payment.get("issue_date")),
                "due_date": self._format_date(payment.get("due_date")),
            }

            for column_index, (_, key, _) in enumerate(self.COLUMNS):
                alignment = Qt.AlignCenter if key in {"id_payment", "id_receipt", "amount"} else Qt.AlignVCenter | Qt.AlignLeft
                self.table.setItem(row_index, column_index, make_table_item(values.get(key, ""), alignment))

        self.table.resizeRowsToContents()

    def _create_summary_card(self, title_text: str, value_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("paymentsSummaryCard")
        card.setMinimumHeight(92)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        title = QLabel(title_text)
        title.setObjectName("paymentsSummaryTitle")

        value = QLabel(value_text)
        value.setObjectName("paymentsSummaryValue")
        value.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(value)
        layout.addStretch()

        card.value_label = value
        return card

    def _update_summary(self, summary: dict):
        self.total_paid_card.value_label.setText(self._format_currency(summary.get("total_paid", 0)))
        self.payment_count_card.value_label.setText(str(summary.get("payment_count", 0)))
        self.last_payment_card.value_label.setText(self._format_date(summary.get("last_payment_date")) or "Sin registros")

        methods = summary.get("methods") or {}
        cash_count = int(methods.get("cash", 0) or 0)
        bank_count = int(methods.get("bank_transfer", 0) or 0)
        card_count = int(methods.get("card", 0) or 0)
        self.methods_card.value_label.setText(
            f"Efectivo: {cash_count} · Transferencia: {bank_count} · Tarjeta: {card_count}"
        )

    def _payment_entity_to_dict(self, payment) -> dict:
        receipt = getattr(payment, "receipt", None)
        enrollment = getattr(receipt, "enrollment", None)
        student = getattr(enrollment, "student", None)
        student_user = getattr(student, "user", None)
        course = getattr(enrollment, "course", None)
        professor = getattr(course, "professor", None)
        professor_user = getattr(professor, "user", None)

        payment_method = getattr(payment, "payment_method", None)
        receipt_status = getattr(receipt, "status", None)

        return {
            "id_payment": getattr(payment, "id_payment", None),
            "payment_date": getattr(payment, "payment_date", None),
            "payment_method_value": self._enum_value(payment_method),
            "id_receipt": getattr(receipt, "id_receipt", None),
            "issue_date": getattr(receipt, "issue_date", None),
            "due_date": getattr(receipt, "due_date", None),
            "amount": getattr(receipt, "amount", 0),
            "receipt_status_value": self._enum_value(receipt_status),
            "id_enrollment": getattr(enrollment, "id_enrollment", None),
            "id_student": getattr(student, "id_student", None),
            "student_name": getattr(student_user, "name", None),
            "student_email": getattr(student_user, "email", None),
            "code_course": getattr(course, "code_course", None),
            "course_name": getattr(course, "name", None),
            "professor_name": getattr(professor_user, "name", None),
            "id_professor": getattr(professor, "id_professor", None),
        }

    def _matches_search(self, payment: dict, search_text: str) -> bool:
        searchable_values = [
            payment.get("id_payment"),
            payment.get("id_receipt"),
            payment.get("id_student"),
            payment.get("student_name"),
            payment.get("student_email"),
            payment.get("code_course"),
            payment.get("course_name"),
            payment.get("id_professor"),
            payment.get("professor_name"),
            self._format_payment_method(payment.get("payment_method_value")),
            self._format_receipt_status(payment.get("receipt_status_value")),
        ]
        return any(search_text in str(value).lower() for value in searchable_values if value is not None)

    def _calculate_summary(self, payments: list[dict]) -> dict:
        total_paid = sum(float(payment.get("amount") or 0) for payment in payments)
        payment_count = len(payments)
        payment_dates = [payment.get("payment_date") for payment in payments if payment.get("payment_date")]
        last_payment_date = max(payment_dates) if payment_dates else None
        methods = {"cash": 0, "bank_transfer": 0, "card": 0}

        for payment in payments:
            method = payment.get("payment_method_value")
            if method in methods:
                methods[method] += 1

        return {
            "total_paid": total_paid,
            "payment_count": payment_count,
            "last_payment_date": last_payment_date,
            "methods": methods,
        }

    def _empty_summary(self) -> dict:
        return {
            "total_paid": 0,
            "payment_count": 0,
            "last_payment_date": None,
            "methods": {"cash": 0, "bank_transfer": 0, "card": 0},
        }

    def _format_payment_method(self, method_value) -> str:
        return self.METHOD_LABELS.get(str(method_value), self._safe_text(method_value))

    def _format_receipt_status(self, status_value) -> str:
        return self.STATUS_LABELS.get(str(status_value), self._safe_text(status_value))

    def _format_currency(self, value) -> str:
        """Formatea valores monetarios para la tabla y las tarjetas resumen."""
        return format_currency(value)

    def _format_date(self, value) -> str:
        """Formatea fechas de forma segura para la interfaz."""
        return format_date(value)

    def _safe_text(self, value) -> str:
        """Retorna texto seguro para celdas vacías."""
        return safe_text(value)

    def _enum_value(self, value):
        """Extrae el valor de Enum sin acoplar la vista al tipo concreto."""
        return enum_value(value)

    def _get_local_styles(self) -> str:
        return """
        QFrame#paymentsFilterPanel,
        QFrame#paymentsTablePanel,
        QFrame#paymentsSummaryCard {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QLabel#paymentsSummaryTitle {
            color: #64748b;
            font-size: 13px;
            font-weight: 700;
        }

        QLabel#paymentsSummaryValue {
            color: #1e3a8a;
            font-size: 19px;
            font-weight: 800;
        }

        QLabel#paymentsSectionTitle {
            color: #0f172a;
            font-size: 18px;
            font-weight: 800;
        }

        QLabel#paymentsCounterLabel {
            color: #475569;
            font-weight: 700;
        }

        QLineEdit#paymentsSearchInput,
        QComboBox#paymentsMethodFilter {
            background-color: #f8fafc;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 9px;
            padding: 8px 10px;
            min-height: 22px;
        }

        QComboBox#paymentsMethodFilter QAbstractItemView {
            background-color: white;
            color: #0f172a;
            selection-background-color: #dbeafe;
            selection-color: #0f172a;
            border: 1px solid #cbd5e1;
        }

        QTableWidget#paymentsTable {
            background-color: white;
            alternate-background-color: #f8fafc;
            gridline-color: #e2e8f0;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            color: #0f172a;
        }
        """


# Alias útil por coherencia con otras vistas administrativas del proyecto.
PaymentsWidget = PaymentsGUI
PaymentManagerWidget = PaymentsGUI
