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


class ProfessorCourseDetailWidget(QWidget):
    """Vista de consulta detallada para cursos asignados al profesor.

    Esta vista corresponde a HU-25 y sirve como punto de entrada para HU-26 y
    HU-27. Muestra la información completa del curso en modo solo lectura y
    mantiene la navegación hacia registro y consulta de notas. La validación de pertenencia del curso al profesor debe
    realizarse desde ProfessorService antes de entregar los datos a esta vista.
    """

    back_requested = Signal()
    grade_registration_requested = Signal(dict)
    grade_record_requested = Signal(dict)

    def __init__(
        self,
        course: dict | None = None,
        on_back: Callable[[], None] | None = None,
        on_register_grades: Callable[[dict], None] | None = None,
        on_view_grade_record: Callable[[dict], None] | None = None,
    ):
        super().__init__()
        self.course = course or {}
        self.on_back = on_back
        self.on_register_grades = on_register_grades
        self.on_view_grade_record = on_view_grade_record

        self.metrics_layout: QHBoxLayout | None = None
        self.academic_grid: QGridLayout | None = None
        self.professor_grid: QGridLayout | None = None
        self.summary_grid: QGridLayout | None = None

        self.setObjectName("professorCourseDetailRoot")
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.set_course(self.course)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("professorDetailHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        title_container = QWidget()
        title_container.setObjectName("professorDetailTitleContainer")
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = QLabel("Detalle del curso")
        self.page_title.setObjectName("professorDetailPageTitle")
        self.page_title.setWordWrap(True)

        self.page_subtitle = QLabel("Consulta la información completa del curso asignado.")
        self.page_subtitle.setObjectName("professorDetailPageSubtitle")
        self.page_subtitle.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)

        self.register_grades_button = QPushButton("Registrar notas")
        self.register_grades_button.setObjectName("professorDetailPrimaryButton")
        self.register_grades_button.setCursor(Qt.PointingHandCursor)
        self.register_grades_button.clicked.connect(self._handle_register_grades)

        self.grade_record_button = QPushButton("Consultar notas")
        self.grade_record_button.setObjectName("professorDetailAccentButton")
        self.grade_record_button.setCursor(Qt.PointingHandCursor)
        self.grade_record_button.clicked.connect(self._handle_grade_record)

        self.back_button = QPushButton("Volver")
        self.back_button.setObjectName("professorDetailSecondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._handle_back)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(self.register_grades_button, 0, Qt.AlignTop)
        header_layout.addWidget(self.grade_record_button, 0, Qt.AlignTop)
        header_layout.addWidget(self.back_button, 0, Qt.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("professorCourseDetailScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("professorCourseDetailScrollContent")
        scroll_layout = QVBoxLayout(self.scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(18)

        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("professorCourseDetailPanel")
        panel_layout = QVBoxLayout(self.detail_panel)
        panel_layout.setContentsMargins(28, 26, 28, 28)
        panel_layout.setSpacing(22)

        self.course_name = QLabel("Curso sin nombre")
        self.course_name.setObjectName("professorCourseDetailName")
        self.course_name.setWordWrap(True)

        self.course_code = QLabel("Código del curso: No registrado")
        self.course_code.setObjectName("professorCourseDetailCode")
        self.course_code.setWordWrap(True)

        self.assignment_banner = QLabel("Curso asignado al profesor autenticado.")
        self.assignment_banner.setObjectName("professorCourseAssignmentBanner")
        self.assignment_banner.setWordWrap(True)

        self.description_section = self._create_section_frame("Descripción general")
        self.description_label = QLabel("No hay descripción registrada para este curso.")
        self.description_label.setObjectName("professorCourseDetailDescription")
        self.description_label.setWordWrap(True)
        self.description_section.layout().addWidget(self.description_label)

        self.metrics_container = QFrame()
        self.metrics_container.setObjectName("professorCourseDetailMetricsContainer")
        self.metrics_layout = QHBoxLayout(self.metrics_container)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.metrics_layout.setSpacing(14)

        self.summary_section = self._create_section_frame("Resumen del curso")
        self.summary_grid = QGridLayout()
        self.summary_grid.setContentsMargins(0, 0, 0, 0)
        self.summary_grid.setHorizontalSpacing(16)
        self.summary_grid.setVerticalSpacing(14)
        self.summary_section.layout().addLayout(self.summary_grid)

        self.academic_section = self._create_section_frame("Información académica")
        self.academic_grid = QGridLayout()
        self.academic_grid.setContentsMargins(0, 0, 0, 0)
        self.academic_grid.setHorizontalSpacing(16)
        self.academic_grid.setVerticalSpacing(14)
        self.academic_section.layout().addLayout(self.academic_grid)

        self.professor_section = self._create_section_frame("Profesor asignado")
        self.professor_grid = QGridLayout()
        self.professor_grid.setContentsMargins(0, 0, 0, 0)
        self.professor_grid.setHorizontalSpacing(16)
        self.professor_grid.setVerticalSpacing(14)
        self.professor_section.layout().addLayout(self.professor_grid)

        panel_layout.addWidget(self.course_name)
        panel_layout.addWidget(self.course_code)
        panel_layout.addWidget(self.assignment_banner)
        panel_layout.addWidget(self.description_section)
        panel_layout.addWidget(self.metrics_container)
        panel_layout.addWidget(self.summary_section)
        panel_layout.addWidget(self.academic_section)
        panel_layout.addWidget(self.professor_section)
        panel_layout.addStretch()

        scroll_layout.addWidget(self.detail_panel)
        scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(header)
        main_layout.addWidget(self.scroll_area, 1)

    def set_course(self, course: dict | None):
        """Carga un curso en la vista y actualiza todos los campos visibles."""
        self.course = course or {}
        self._refresh_course_data()
        self._reset_scroll_position()

    def set_back_callback(self, callback: Callable[[], None] | None):
        """Define la acción que se ejecuta al pulsar el botón Volver."""
        self.on_back = callback

    def set_register_grades_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que abre el registro de notas del curso actual."""
        self.on_register_grades = callback

    def set_grade_record_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que abre la planilla de notas del curso actual."""
        self.on_view_grade_record = callback

    def _refresh_course_data(self):
        course_name = self._read("name", default="Curso sin nombre")
        code_course = self._read("code_course", "course_code", default="No registrado")
        description = self._read("description", default="No hay descripción registrada para este curso.")

        self.page_title.setText(course_name)
        self.course_name.setText(course_name)
        self.course_code.setText(f"Código del curso: {code_course}")
        self.description_label.setText(description)

        self._refresh_metrics()
        self._refresh_summary_info()
        self._refresh_academic_info()
        self._refresh_professor_info()

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

    def _refresh_summary_info(self):
        self._clear_grid(self.summary_grid)

        rows = [
            ("Nombre", self._read("name", default="No registrado")),
            ("Código", self._read("code_course", "course_code", default="No registrado")),
            ("Estudiantes inscritos", self._format_students(self._read("enrolled_students", "students", default=""))),
            ("Costo", self._format_price(self.course.get("price"))),
        ]

        self._populate_grid(self.summary_grid, rows)

    def _refresh_academic_info(self):
        self._clear_grid(self.academic_grid)

        rows = [
            ("Horario", self._read("schedule", default="No registrado")),
            ("Ubicación", self._read("location", default="No registrada")),
            ("Fecha de inicio", self._format_date(self.course.get("start_date"))),
            ("Fecha de finalización", self._format_date(self.course.get("end_date"))),
            ("Duración", self._format_days(self.course.get("duration_days"))),
            ("Intensidad horaria", self._format_hours(self.course.get("intensity_hours"))),
        ]

        self._populate_grid(self.academic_grid, rows)

    def _refresh_professor_info(self):
        self._clear_grid(self.professor_grid)

        professor = self.course.get("professor")
        if not isinstance(professor, dict):
            professor = {}

        rows = [
            ("Identificación", self._read_nested(professor, "id_professor", default=self._read("id_professor", default="No registrada"))),
            ("Nombre", self._read_nested(professor, "name", default="No registrado")),
            ("Correo", self._read_nested(professor, "email", default="No registrado")),
            ("Título profesional", self._read_nested(professor, "professional_title", default="No registrado")),
        ]

        self._populate_grid(self.professor_grid, rows)

    def _populate_grid(self, grid: QGridLayout, rows: list[tuple[str, str]]):
        for index, (label, value) in enumerate(rows):
            item = self._create_info_item(label, value)
            row = index // 2
            column = index % 2
            grid.addWidget(item, row, column)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

    def _create_section_frame(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("professorCourseDetailSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        label = QLabel(title)
        label.setObjectName("professorCourseDetailSectionTitle")
        layout.addWidget(label)

        return frame

    def _create_metric_card(self, label: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("professorCourseDetailMetricCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        value_label = QLabel(str(value))
        value_label.setObjectName("professorCourseDetailMetricValue")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setWordWrap(True)

        name_label = QLabel(str(label))
        name_label.setObjectName("professorCourseDetailMetricLabel")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)

        layout.addWidget(value_label)
        layout.addWidget(name_label)

        return frame

    def _create_info_item(self, label: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("professorCourseDetailInfoItem")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        label_widget = QLabel(str(label))
        label_widget.setObjectName("professorCourseDetailInfoLabel")
        label_widget.setWordWrap(True)

        value_widget = QLabel(str(value))
        value_widget.setObjectName("professorCourseDetailInfoValue")
        value_widget.setWordWrap(True)
        value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return frame

    def _handle_back(self):
        self.back_requested.emit()
        if callable(self.on_back):
            self.on_back()

    def _handle_register_grades(self):
        self.grade_registration_requested.emit(self.course)
        if callable(self.on_register_grades):
            self.on_register_grades(self.course)

    def _handle_grade_record(self):
        self.grade_record_requested.emit(self.course)
        if callable(self.on_view_grade_record):
            self.on_view_grade_record(self.course)

    def _reset_scroll_position(self):
        if hasattr(self, "scroll_area") and self.scroll_area is not None:
            self.scroll_area.verticalScrollBar().setValue(0)
            self.scroll_area.horizontalScrollBar().setValue(0)

    def _read(self, *keys: str, default: str = ""):
        for key in keys:
            value = self.course.get(key)
            if value not in (None, ""):
                return str(value).strip()
        return default

    @staticmethod
    def _read_nested(data: dict, *keys: str, default: str = ""):
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return str(value).strip()
        return default

    @staticmethod
    def _format_price(value) -> str:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return "No registrado"

        if amount <= 0:
            return "No registrado"

        return f"${amount:,.2f}"

    @staticmethod
    def _format_days(value) -> str:
        try:
            days = int(float(value))
        except (TypeError, ValueError):
            return "No registrada"

        if days <= 0:
            return "No registrada"

        unit = "día" if days == 1 else "días"
        return f"{days} {unit}"

    @staticmethod
    def _format_hours(value) -> str:
        try:
            hours = float(value)
        except (TypeError, ValueError):
            return "No registrada"

        if hours <= 0:
            return "No registrada"

        if hours.is_integer():
            hours = int(hours)

        unit = "hora" if hours == 1 else "horas"
        return f"{hours} {unit}"

    @staticmethod
    def _format_students(value) -> str:
        try:
            students = int(float(value))
        except (TypeError, ValueError):
            students = 0

        unit = "estudiante" if students == 1 else "estudiantes"
        return f"{students} {unit}"

    @staticmethod
    def _format_date(value) -> str:
        text = str(value or "").strip()
        return text or "No registrada"

    @staticmethod
    def _clear_layout(layout):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                ProfessorCourseDetailWidget._clear_layout(child_layout)

    @staticmethod
    def _clear_grid(grid: QGridLayout | None):
        if grid is None:
            return

        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                ProfessorCourseDetailWidget._clear_layout(child_layout)

    @staticmethod
    def get_styles() -> str:
        return """
        QWidget#professorCourseDetailRoot,
        QWidget#professorCourseDetailScrollContent {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#professorDetailHeader {
            background-color: transparent;
            border: none;
        }

        QLabel#professorDetailPageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 800;
        }

        QLabel#professorDetailPageSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QPushButton#professorDetailPrimaryButton {
            background-color: #2563eb;
            color: white;
            border: 1px solid #1d4ed8;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 800;
        }

        QPushButton#professorDetailPrimaryButton:hover {
            background-color: #1d4ed8;
            border-color: #1e40af;
        }

        QPushButton#professorDetailAccentButton {
            background-color: #eef4ff;
            color: #1e3a8a;
            border: 1px solid #bfdbfe;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 800;
        }

        QPushButton#professorDetailAccentButton:hover {
            background-color: #dbeafe;
            border-color: #93c5fd;
        }

        QPushButton#professorDetailSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 700;
        }

        QPushButton#professorDetailSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QScrollArea#professorCourseDetailScrollArea {
            background-color: transparent;
            border: none;
        }

        QFrame#professorCourseDetailPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QLabel#professorCourseDetailName {
            color: #0f172a;
            font-size: 24px;
            font-weight: 800;
        }

        QLabel#professorCourseDetailCode {
            color: #1e3a8a;
            font-size: 14px;
            font-weight: 800;
        }

        QLabel#professorCourseAssignmentBanner {
            background-color: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QFrame#professorCourseDetailSection {
            background-color: #f8fbff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
        }

        QLabel#professorCourseDetailSectionTitle {
            color: #1e3a8a;
            font-size: 17px;
            font-weight: 800;
        }

        QLabel#professorCourseDetailDescription {
            color: #334155;
            line-height: 1.35;
        }

        QFrame#professorCourseDetailMetricsContainer {
            background-color: transparent;
            border: none;
        }

        QFrame#professorCourseDetailMetricCard {
            background-color: #eef4ff;
            border: 1px solid #dbeafe;
            border-radius: 14px;
        }

        QLabel#professorCourseDetailMetricValue {
            color: #0f172a;
            font-size: 18px;
            font-weight: 800;
        }

        QLabel#professorCourseDetailMetricLabel {
            color: #475569;
            font-size: 12px;
            font-weight: 700;
        }

        QFrame#professorCourseDetailInfoItem {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }

        QLabel#professorCourseDetailInfoLabel {
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
        }

        QLabel#professorCourseDetailInfoValue {
            color: #0f172a;
            font-size: 14px;
            font-weight: 700;
        }

        QScrollBar:vertical, QScrollBar:horizontal {
            background-color: #f1f5f9;
            border: none;
            margin: 0px;
        }

        QScrollBar:vertical {
            width: 10px;
        }

        QScrollBar:horizontal {
            height: 10px;
        }

        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background-color: #94a3b8;
            border-radius: 5px;
            min-height: 28px;
            min-width: 28px;
        }

        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background-color: #64748b;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            width: 0px;
            height: 0px;
        }
        """
