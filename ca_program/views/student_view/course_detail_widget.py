from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class CourseDetailWidget(QWidget):
    """Vista de consulta detallada para un curso.

    Esta vista pertenece a HU-20 y se amplía para HU-21. Presenta la
    información completa del curso en modo solo lectura y muestra una acción
    contextual para inscribirse o pagar el recibo pendiente cuando corresponda.
    """

    STATUS_NOT_ENROLLED = "NO_INSCRITO"
    STATUS_PENDING_PAYMENT = "PENDIENTE_DE_PAGO"
    STATUS_ENROLLED = "INSCRITO"
    STATUS_EXPIRED = "VENCIDO"

    back_requested = Signal()

    def __init__(
        self,
        course: dict | None = None,
        on_back: Callable[[], None] | None = None,
        on_enroll_course: Callable[[dict], None] | None = None,
        on_pay_course: Callable[[dict], None] | None = None,
    ):
        super().__init__()
        self.course = course or {}
        self.on_back = on_back
        self.on_enroll_course = on_enroll_course
        self.on_pay_course = on_pay_course
        self.current_action: str | None = None

        self.info_grid: QGridLayout | None = None
        self.professor_grid: QGridLayout | None = None
        self.enrollment_grid: QGridLayout | None = None
        self.metrics_layout: QHBoxLayout | None = None
        self.action_button: QPushButton | None = None

        self.setObjectName("courseDetailRoot")
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.set_course(self.course)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("studentHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = QLabel("Detalle del curso")
        self.page_title.setObjectName("studentPageTitle")
        self.page_title.setWordWrap(True)

        self.page_subtitle = QLabel("Consulta la información completa del curso seleccionado.")
        self.page_subtitle.setObjectName("studentPageSubtitle")
        self.page_subtitle.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)

        self.action_button = QPushButton("Inscribirme")
        self.action_button.setObjectName("enrollButton")
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.clicked.connect(self._handle_course_action)
        self.action_button.hide()

        self.back_button = QPushButton("Volver")
        self.back_button.setObjectName("secondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._handle_back)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(self.action_button, 0, Qt.AlignTop)
        header_layout.addWidget(self.back_button, 0, Qt.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("courseDetailScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("courseDetailScrollContent")
        scroll_layout = QVBoxLayout(self.scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(18)

        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("courseDetailPanel")
        panel_layout = QVBoxLayout(self.detail_panel)
        panel_layout.setContentsMargins(28, 26, 28, 28)
        panel_layout.setSpacing(22)

        self.course_name = QLabel("Curso sin nombre")
        self.course_name.setObjectName("courseDetailName")
        self.course_name.setWordWrap(True)

        self.course_code = QLabel("Código no registrado")
        self.course_code.setObjectName("courseDetailCode")
        self.course_code.setWordWrap(True)

        self.status_banner = QLabel("Disponible para inscripción")
        self.status_banner.setObjectName("courseStatusBanner")
        self.status_banner.setWordWrap(True)

        self.description_section = self._create_section_frame("Descripción general")
        self.description_label = QLabel("No hay descripción registrada para este curso.")
        self.description_label.setObjectName("courseDetailDescription")
        self.description_label.setWordWrap(True)
        self.description_section.layout().addWidget(self.description_label)

        self.metrics_container = QFrame()
        self.metrics_container.setObjectName("courseDetailMetricsContainer")
        self.metrics_layout = QHBoxLayout(self.metrics_container)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.metrics_layout.setSpacing(14)

        self.enrollment_section = self._create_section_frame("Estado de inscripción")
        self.enrollment_grid = QGridLayout()
        self.enrollment_grid.setContentsMargins(0, 0, 0, 0)
        self.enrollment_grid.setHorizontalSpacing(16)
        self.enrollment_grid.setVerticalSpacing(14)
        self.enrollment_section.layout().addLayout(self.enrollment_grid)

        self.info_section = self._create_section_frame("Información académica")
        self.info_grid = QGridLayout()
        self.info_grid.setContentsMargins(0, 0, 0, 0)
        self.info_grid.setHorizontalSpacing(16)
        self.info_grid.setVerticalSpacing(14)
        self.info_section.layout().addLayout(self.info_grid)

        self.professor_section = self._create_section_frame("Profesor asignado")
        self.professor_grid = QGridLayout()
        self.professor_grid.setContentsMargins(0, 0, 0, 0)
        self.professor_grid.setHorizontalSpacing(16)
        self.professor_grid.setVerticalSpacing(14)
        self.professor_section.layout().addLayout(self.professor_grid)

        panel_layout.addWidget(self.course_name)
        panel_layout.addWidget(self.course_code)
        panel_layout.addWidget(self.status_banner)
        panel_layout.addWidget(self.description_section)
        panel_layout.addWidget(self.metrics_container)
        panel_layout.addWidget(self.enrollment_section)
        panel_layout.addWidget(self.info_section)
        panel_layout.addWidget(self.professor_section)
        panel_layout.addStretch()

        scroll_layout.addWidget(self.detail_panel)
        scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(header)
        main_layout.addWidget(self.scroll_area, 1)

    def set_course(self, course: dict | None):
        self.course = course or {}
        self._refresh_course_data()

    def set_enroll_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que se ejecuta al solicitar inscripción."""
        self.on_enroll_course = callback
        self._refresh_course_action()

    def set_payment_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que se ejecuta al pagar un recibo pendiente."""
        self.on_pay_course = callback
        self._refresh_course_action()

    def set_course_action_callbacks(
        self,
        on_enroll_course: Callable[[dict], None] | None = None,
        on_pay_course: Callable[[dict], None] | None = None,
    ):
        """Configura las acciones de HU-21 desde StudentGUI."""
        self.on_enroll_course = on_enroll_course
        self.on_pay_course = on_pay_course
        self._refresh_course_action()

    def _refresh_course_data(self):
        course_name = self._read("name", default="Curso sin nombre")
        code_course = self._read("code_course", "course_code", default="No registrado")
        description = self._read("description", default="No hay descripción registrada para este curso.")

        self.page_title.setText(course_name)
        self.course_name.setText(course_name)
        self.course_code.setText(f"Código del curso: {code_course}")
        self.description_label.setText(description)

        self._refresh_metrics()
        self._refresh_enrollment_status()
        self._refresh_academic_info()
        self._refresh_professor_info()
        self._refresh_course_action()

    def _refresh_metrics(self):
        self._clear_layout(self.metrics_layout)

        metrics = [
            ("Costo", self._format_price(self.course.get("price"))),
            ("Duración", self._format_days(self.course.get("duration_days"))),
            ("Intensidad", self._format_hours(self.course.get("intensity_hours"))),
            ("Estudiantes", self._format_students(self._read("enrolled_students", "students", default=""))),
        ]

        for label, value in metrics:
            self.metrics_layout.addWidget(self._create_metric_card(label, value), 1)

    def _refresh_enrollment_status(self):
        self._clear_grid(self.enrollment_grid)

        status = self._normalize_status(self.course.get("enrollment_status"))
        receipt = self.course.get("receipt")

        if status == self.STATUS_ENROLLED:
            banner_text = "Inscripción confirmada. Este curso ya forma parte de tus cursos."
            rows = [
                ("Estado", "Inscrito"),
                ("Acción disponible", "Consulta del curso"),
            ]
        elif status == self.STATUS_PENDING_PAYMENT:
            banner_text = "Tienes un recibo pendiente. Realiza el pago para completar la inscripción."
            rows = [
                ("Estado", "Pendiente de pago"),
                ("Valor del recibo", self._format_price(self._read_receipt(receipt, "amount", default=self.course.get("price")))),
                ("Fecha de emisión", self._format_date(self._read_receipt(receipt, "issue_date", default=""))),
                ("Fecha límite", self._format_date(self._read_receipt(receipt, "due_date", default=""))),
            ]
        elif status == self.STATUS_EXPIRED:
            banner_text = "El recibo pendiente venció. Puedes solicitar nuevamente la inscripción."
            rows = [
                ("Estado", "Recibo vencido"),
                ("Acción disponible", "Nueva solicitud de inscripción"),
            ]
        else:
            banner_text = "Disponible para inscripción. Revisa los datos antes de iniciar el proceso."
            rows = [
                ("Estado", "Disponible"),
                ("Acción disponible", "Solicitar inscripción"),
            ]

        self.status_banner.setText(banner_text)
        self.status_banner.setObjectName(self._get_status_banner_object_name(status))
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

        for index, (label, value) in enumerate(rows):
            row = index // 2
            column = index % 2
            self.enrollment_grid.addWidget(self._create_info_block(label, value), row, column)

        self.enrollment_grid.setColumnStretch(0, 1)
        self.enrollment_grid.setColumnStretch(1, 1)

    def _refresh_academic_info(self):
        self._clear_grid(self.info_grid)

        rows = [
            ("Horario", self._read("schedule", default="No registrado")),
            ("Ubicación", self._read("location", default="No registrada")),
            ("Fecha de inicio", self._format_date(self.course.get("start_date"))),
            ("Fecha de finalización", self._format_date(self.course.get("end_date"))),
        ]

        for index, (label, value) in enumerate(rows):
            row = index // 2
            column = index % 2
            self.info_grid.addWidget(self._create_info_block(label, value), row, column)

        self.info_grid.setColumnStretch(0, 1)
        self.info_grid.setColumnStretch(1, 1)

    def _refresh_professor_info(self):
        self._clear_grid(self.professor_grid)

        rows = [
            ("Nombre", self._read_professor("name", default="Sin profesor asignado")),
            ("Título profesional", self._read_professor("professional_title", default="No registrado")),
            ("Correo", self._read_professor("email", default="No registrado")),
            ("Identificación", self._read_professor("id_professor", default="No registrada")),
        ]

        for index, (label, value) in enumerate(rows):
            row = index // 2
            column = index % 2
            self.professor_grid.addWidget(self._create_info_block(label, value), row, column)

        self.professor_grid.setColumnStretch(0, 1)
        self.professor_grid.setColumnStretch(1, 1)

    def _refresh_course_action(self):
        if self.action_button is None:
            return

        status = self._normalize_status(self.course.get("enrollment_status"))
        self.current_action = None

        if status in {self.STATUS_NOT_ENROLLED, self.STATUS_EXPIRED} and callable(self.on_enroll_course):
            self.current_action = "enroll"
            self.action_button.setText("Inscribirme")
            self.action_button.setObjectName("enrollButton")
            self.action_button.setEnabled(True)
            self.action_button.show()
        elif status == self.STATUS_PENDING_PAYMENT and callable(self.on_pay_course):
            self.current_action = "payment"
            self.action_button.setText("Pagar recibo")
            self.action_button.setObjectName("paymentButton")
            self.action_button.setEnabled(True)
            self.action_button.show()
        else:
            self.action_button.hide()

        self.action_button.style().unpolish(self.action_button)
        self.action_button.style().polish(self.action_button)

    def _create_section_frame(self, title: str) -> QFrame:
        section = QFrame()
        section.setObjectName("courseDetailSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        section_title = QLabel(title)
        section_title.setObjectName("courseDetailSectionTitle")
        layout.addWidget(section_title)

        return section

    def _create_metric_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("courseMetricCard")
        card.setMinimumHeight(86)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        label_widget = QLabel(label)
        label_widget.setObjectName("courseMetricLabel")

        value_widget = QLabel(value)
        value_widget.setObjectName("courseMetricValue")
        value_widget.setWordWrap(True)

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        layout.addStretch()

        return card

    def _create_info_block(self, label: str, value: str) -> QFrame:
        block = QFrame()
        block.setObjectName("courseInfoBlock")
        block.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(block)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)

        label_widget = QLabel(label)
        label_widget.setObjectName("courseInfoLabel")

        value_widget = QLabel(str(value) if value not in (None, "") else "No registrado")
        value_widget.setObjectName("courseInfoValue")
        value_widget.setWordWrap(True)

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return block

    def _handle_back(self):
        if self.on_back:
            self.on_back()
        self.back_requested.emit()

    def _handle_course_action(self):
        if self.current_action == "enroll" and callable(self.on_enroll_course):
            self.on_enroll_course(self.course)
            return

        if self.current_action == "payment" and callable(self.on_pay_course):
            self.on_pay_course(self.course)

    def _read(self, *keys: str, default="No registrado"):
        for key in keys:
            value = self.course.get(key)
            if value not in (None, ""):
                return value
        return default

    def _read_professor(self, key: str, default: str = "No registrado") -> str:
        professor = self.course.get("professor") or {}
        value = professor.get(key)
        if value not in (None, ""):
            return str(value).strip()
        return default

    def _read_receipt(self, receipt, key: str, default=""):
        if receipt in (None, ""):
            return default

        if isinstance(receipt, dict):
            return receipt.get(key, default)

        return getattr(receipt, key, default)

    def _get_status_banner_object_name(self, status: str) -> str:
        if status == self.STATUS_ENROLLED:
            return "courseStatusBannerEnrolled"
        if status == self.STATUS_PENDING_PAYMENT:
            return "courseStatusBannerPending"
        if status == self.STATUS_EXPIRED:
            return "courseStatusBannerExpired"
        return "courseStatusBanner"

    def _normalize_status(self, status) -> str:
        status_text = str(status or self.STATUS_NOT_ENROLLED).strip().upper()

        aliases = {
            "NOT_ENROLLED": self.STATUS_NOT_ENROLLED,
            "NO INSCRITO": self.STATUS_NOT_ENROLLED,
            "DISPONIBLE": self.STATUS_NOT_ENROLLED,
            "PENDING_PAYMENT": self.STATUS_PENDING_PAYMENT,
            "PENDIENTE": self.STATUS_PENDING_PAYMENT,
            "PENDIENTE DE PAGO": self.STATUS_PENDING_PAYMENT,
            "ENROLLED": self.STATUS_ENROLLED,
            "CONFIRMADO": self.STATUS_ENROLLED,
            "VENCIDO": self.STATUS_EXPIRED,
            "EXPIRED": self.STATUS_EXPIRED,
            "ESTADO_NO_DISPONIBLE": "ESTADO_NO_DISPONIBLE",
        }

        return aliases.get(status_text, status_text)

    def _format_price(self, price) -> str:
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            return "No registrado"

        if numeric_price <= 0:
            return "No registrado"

        formatted = f"{numeric_price:,.0f}".replace(",", ".")
        return f"$ {formatted}"

    def _format_days(self, days) -> str:
        try:
            numeric_days = int(days)
        except (TypeError, ValueError):
            return "No registrada"

        if numeric_days <= 0:
            return "No registrada"

        return f"{numeric_days} día" if numeric_days == 1 else f"{numeric_days} días"

    def _format_hours(self, hours) -> str:
        try:
            numeric_hours = int(hours)
        except (TypeError, ValueError):
            return "No registrada"

        if numeric_hours <= 0:
            return "No registrada"

        return f"{numeric_hours} hora" if numeric_hours == 1 else f"{numeric_hours} horas"

    def _format_students(self, students) -> str:
        try:
            numeric_students = int(students)
        except (TypeError, ValueError):
            return "No registrado"

        return f"{numeric_students} estudiante" if numeric_students == 1 else f"{numeric_students} estudiantes"

    def _format_date(self, value) -> str:
        if value in (None, ""):
            return "No registrada"

        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y")

        return str(value).strip()

    def _clear_grid(self, grid: QGridLayout | None):
        if grid is None:
            return

        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _clear_layout(self, layout: QHBoxLayout | QVBoxLayout | None):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def get_styles(self) -> str:
        return """
        QWidget#courseDetailRoot, QWidget#courseDetailScrollContent {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QScrollArea#courseDetailScrollArea {
            background-color: transparent;
            border: none;
        }

        QFrame#courseDetailPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QLabel#courseDetailName {
            color: #0f172a;
            font-size: 30px;
            font-weight: 900;
        }

        QLabel#courseDetailCode {
            color: #475569;
            font-size: 14px;
            font-weight: 700;
        }

        QLabel#courseStatusBanner,
        QLabel#courseStatusBannerPending,
        QLabel#courseStatusBannerEnrolled,
        QLabel#courseStatusBannerExpired {
            border-radius: 14px;
            font-size: 14px;
            font-weight: 800;
            padding: 12px 14px;
        }

        QLabel#courseStatusBanner {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1e3a8a;
        }

        QLabel#courseStatusBannerPending {
            background-color: #fffbeb;
            border: 1px solid #fde68a;
            color: #92400e;
        }

        QLabel#courseStatusBannerEnrolled {
            background-color: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #166534;
        }

        QLabel#courseStatusBannerExpired {
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
        }

        QFrame#courseDetailSection {
            background-color: #f8fbff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
        }

        QLabel#courseDetailSectionTitle {
            color: #1e3a8a;
            font-size: 17px;
            font-weight: 900;
        }

        QLabel#courseDetailDescription {
            color: #334155;
            font-size: 14px;
            line-height: 150%;
        }

        QFrame#courseMetricCard {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 14px;
        }

        QLabel#courseMetricLabel {
            color: #475569;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#courseMetricValue {
            color: #1e3a8a;
            font-size: 18px;
            font-weight: 900;
        }

        QFrame#courseInfoBlock {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }

        QLabel#courseInfoLabel {
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#courseInfoValue {
            color: #0f172a;
            font-size: 14px;
            font-weight: 700;
        }

        QPushButton#secondaryButton {
            background-color: #e2e8f0;
            color: #1e293b;
            border: none;
            padding: 10px 16px;
            border-radius: 10px;
            font-weight: 800;
        }

        QPushButton#secondaryButton:hover {
            background-color: #cbd5e1;
        }

        QPushButton#enrollButton {
            background-color: #16a34a;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 10px;
            font-weight: 900;
        }

        QPushButton#enrollButton:hover {
            background-color: #15803d;
        }

        QPushButton#paymentButton {
            background-color: #f59e0b;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 10px;
            font-weight: 900;
        }

        QPushButton#paymentButton:hover {
            background-color: #d97706;
        }
        """
