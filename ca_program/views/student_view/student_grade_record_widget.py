from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.grade_service import GradeService


class StudentGradeRecordWidget(QWidget):
    """Vista de consulta del registro de notas para usuarios estudiantes.

    HU-23: permite que el estudiante autenticado consulte sus propias notas
    en los cursos donde tiene inscripción confirmada. La vista es de solo
    lectura: no registra, no modifica y no elimina calificaciones.
    """

    COL_CODE = 0
    COL_COURSE = 1
    COL_PROFESSOR = 2
    COL_GRADE1 = 3
    COL_GRADE2 = 4
    COL_GRADE3 = 5
    COL_AVERAGE = 6
    COL_STATUS = 7

    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.grade_records: list[dict] = []
        self.summary: dict = {}

        self.setObjectName("studentGradeRecordRoot")
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.load_records(show_error=False)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("studentGradeHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = QLabel("Mis notas")
        self.page_title.setObjectName("studentGradePageTitle")
        self.page_title.setWordWrap(True)

        self.page_subtitle = QLabel(
            "Consulta tus calificaciones registradas y el estado académico de tus cursos inscritos."
        )
        self.page_subtitle.setObjectName("studentGradePageSubtitle")
        self.page_subtitle.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)

        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setObjectName("studentGradeSecondaryButton")
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.load_records)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(self.refresh_button, 0, Qt.AlignTop)

        self.summary_panel = QFrame()
        self.summary_panel.setObjectName("studentGradeSummaryPanel")
        summary_layout = QHBoxLayout(self.summary_panel)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(14)

        self.card_enrolled = self._create_summary_card("Cursos inscritos", "0")
        self.card_graded = self._create_summary_card("Cursos calificados", "0")
        self.card_average = self._create_summary_card("Promedio general", "0.00")
        self.card_approved = self._create_summary_card("Aprobados", "0")
        self.card_pending = self._create_summary_card("Pendientes", "0")

        summary_layout.addWidget(self.card_enrolled["frame"])
        summary_layout.addWidget(self.card_graded["frame"])
        summary_layout.addWidget(self.card_average["frame"])
        summary_layout.addWidget(self.card_approved["frame"])
        summary_layout.addWidget(self.card_pending["frame"])

        self.info_label = QLabel(
            "La información se muestra en modo consulta. Las notas pendientes aparecerán cuando el profesor registre la calificación del curso."
        )
        self.info_label.setObjectName("studentGradeInfoLabel")
        self.info_label.setWordWrap(True)

        controls_panel = QFrame()
        controls_panel.setObjectName("studentGradeControlsPanel")
        controls_layout = QHBoxLayout(controls_panel)
        controls_layout.setContentsMargins(16, 14, 16, 14)
        controls_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("studentGradeSearchInput")
        self.search_input.setPlaceholderText("Buscar por curso, profesor, código o estado")
        self.search_input.textChanged.connect(self._apply_filter)

        self.visible_count_label = QLabel("Registros visibles: 0")
        self.visible_count_label.setObjectName("studentGradeVisibleCount")

        controls_layout.addWidget(self.search_input, 1)
        controls_layout.addWidget(self.visible_count_label, 0)

        self.table_panel = QFrame()
        self.table_panel.setObjectName("studentGradeTablePanel")
        table_layout = QVBoxLayout(self.table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.table = QTableWidget(0, 8)
        self.table.setObjectName("studentGradeTable")
        self.table.setHorizontalHeaderLabels([
            "Código",
            "Curso",
            "Profesor",
            "Nota 1",
            "Nota 2",
            "Nota 3",
            "Promedio",
            "Estado",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.setWordWrap(True)

        header_view = self.table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(self.COL_CODE, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_COURSE, QHeaderView.Stretch)
        header_view.setSectionResizeMode(self.COL_PROFESSOR, QHeaderView.Stretch)
        header_view.setSectionResizeMode(self.COL_GRADE1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_GRADE2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_GRADE3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_AVERAGE, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_STATUS, QHeaderView.Fixed)
        self.table.setColumnWidth(self.COL_STATUS, 128)

        table_layout.addWidget(self.table)

        self.empty_label = QLabel("Aún no tienes cursos confirmados con registro académico disponible.")
        self.empty_label.setObjectName("studentGradeEmptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()

        main_layout.addWidget(header)
        main_layout.addWidget(self.summary_panel)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(controls_panel)
        main_layout.addWidget(self.table_panel, 1)
        main_layout.addWidget(self.empty_label, 1)

        self._refresh_summary({})

    def _create_summary_card(self, label: str, value: str) -> dict:
        frame = QFrame()
        frame.setObjectName("studentGradeSummaryCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("studentGradeSummaryValue")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setWordWrap(True)

        title_label = QLabel(label)
        title_label.setObjectName("studentGradeSummaryTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)

        layout.addWidget(value_label)
        layout.addWidget(title_label)

        return {
            "frame": frame,
            "value": value_label,
            "title": title_label,
        }

    def set_user(self, user):
        self.user = user
        self.load_records(show_error=False)

    def load_records(self, show_error: bool = True):
        result = GradeService.get_student_grade_record(user=self.user)

        if not result.get("success"):
            self.grade_records = []
            self.summary = result.get("summary") or {}
            self._refresh_summary(self.summary)
            self._render_records(
                empty_message="No fue posible cargar tu registro de notas."
            )

            if show_error:
                QMessageBox.warning(
                    self,
                    "No fue posible consultar tus notas",
                    result.get("message", "Ocurrió un error al consultar el registro de notas."),
                )
            return

        records = result.get("grades") or result.get("grade_records") or result.get("data") or []
        self.grade_records = [self._normalize_record(record) for record in records]
        self.summary = result.get("summary") or {}
        self._refresh_summary(self.summary)
        self._render_records()

    def _render_records(self, empty_message: str | None = None):
        self.table.setRowCount(0)
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)

        if not self.grade_records:
            self.table_panel.hide()
            self.empty_label.setText(
                empty_message
                or "Aún no tienes cursos confirmados con registro académico disponible."
            )
            self.empty_label.show()
            self.visible_count_label.setText("Registros visibles: 0")
            return

        self.empty_label.hide()
        self.table_panel.show()
        self.table.setRowCount(len(self.grade_records))

        for row, record in enumerate(self.grade_records):
            self._set_item(row, self.COL_CODE, record.get("code_course", ""), align=Qt.AlignCenter)
            self._set_item(row, self.COL_COURSE, record.get("course_name", ""))
            self._set_item(row, self.COL_PROFESSOR, record.get("professor_name", ""))
            self._set_item(row, self.COL_GRADE1, self._format_grade(record.get("grade1")), align=Qt.AlignCenter)
            self._set_item(row, self.COL_GRADE2, self._format_grade(record.get("grade2")), align=Qt.AlignCenter)
            self._set_item(row, self.COL_GRADE3, self._format_grade(record.get("grade3")), align=Qt.AlignCenter)
            self._set_item(row, self.COL_AVERAGE, self._format_average(record.get("average")), align=Qt.AlignCenter)
            self._set_status_badge(row, record)

            search_blob = " ".join([
                str(record.get("code_course", "")),
                str(record.get("course_name", "")),
                str(record.get("professor_name", "")),
                str(record.get("status_label", "")),
            ]).lower()
            self.table.item(row, self.COL_CODE).setData(Qt.UserRole, search_blob)

        self._apply_filter()
        QTimer.singleShot(0, lambda: self.table.scrollToTop())

    def _set_item(self, row: int, column: int, value, align=Qt.AlignLeft | Qt.AlignVCenter):
        item = QTableWidgetItem(str(value if value not in (None, "") else "—"))
        item.setTextAlignment(align)
        self.table.setItem(row, column, item)

    def _set_status_badge(self, row: int, record: dict):
        status_value = str(record.get("status", "pending")).strip().lower()
        status_label = self._status_to_label(status_value)

        badge = QLabel(status_label)
        badge.setAlignment(Qt.AlignCenter)
        badge.setObjectName(self._status_badge_name(status_value, status_label))
        badge.setMinimumWidth(108)
        badge.setMinimumHeight(28)
        badge.setMargin(2)

        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        layout.addWidget(badge, 0, Qt.AlignCenter)

        self.table.setCellWidget(row, self.COL_STATUS, wrapper)

        status_item = QTableWidgetItem(status_label)
        status_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, self.COL_STATUS, status_item)
        self.table.setCellWidget(row, self.COL_STATUS, wrapper)

    def _apply_filter(self):
        query = self.search_input.text().strip().lower()
        visible = 0

        for row in range(self.table.rowCount()):
            item = self.table.item(row, self.COL_CODE)
            search_blob = str(item.data(Qt.UserRole) if item else "").lower()
            should_show = not query or query in search_blob
            self.table.setRowHidden(row, not should_show)
            if should_show:
                visible += 1

        self.visible_count_label.setText(f"Registros visibles: {visible}")

        if self.grade_records and visible == 0:
            self.empty_label.setText("No hay registros que coincidan con la búsqueda.")
            self.empty_label.show()
        elif self.grade_records:
            self.empty_label.hide()

    def _refresh_summary(self, summary: dict):
        total_enrolled = self._read_summary(summary, "total_enrolled", "total_courses")
        total_graded = self._read_summary(summary, "total_graded", "graded")
        general_average = self._read_summary(summary, "general_average", "academic_average")
        approved = self._read_summary(summary, "approved")
        pending = self._read_summary(summary, "pending")

        self.card_enrolled["value"].setText(str(total_enrolled or 0))
        self.card_graded["value"].setText(str(total_graded or 0))
        self.card_average["value"].setText(self._format_average(general_average))
        self.card_approved["value"].setText(str(approved or 0))
        self.card_pending["value"].setText(str(pending or 0))

    @staticmethod
    def _read_summary(summary: dict, *keys):
        for key in keys:
            value = (summary or {}).get(key)
            if value not in (None, ""):
                return value
        return 0

    def _normalize_record(self, record: dict) -> dict:
        if not isinstance(record, dict):
            return {}

        course = record.get("course") or {}
        professor = record.get("professor") or course.get("professor") or {}

        has_grade = bool(record.get("has_grade"))
        status = str(record.get("status", "pending") or "pending").strip().lower()
        if not has_grade:
            status = "pending"
        status_label = self._status_to_label(status)

        return {
            "id_enrollment": record.get("id_enrollment", ""),
            "id_grade": record.get("id_grade", ""),
            "code_course": record.get("code_course") or course.get("code_course") or "",
            "course_name": record.get("course_name") or course.get("name") or "Curso sin nombre",
            "professor_name": record.get("professor_name") or professor.get("name") or "No asignado",
            "has_grade": has_grade,
            "grade1": record.get("grade1", ""),
            "grade2": record.get("grade2", ""),
            "grade3": record.get("grade3", ""),
            "average": record.get("average", ""),
            "status": status,
            "status_label": status_label,
            "raw": record,
        }

    @staticmethod
    def _status_to_label(status: str) -> str:
        status = str(status or "pending").strip().lower()
        if status == "passed":
            return "Aprobado"
        if status == "failed":
            return "Reprobado"
        return "Pendiente"

    @staticmethod
    def _status_badge_name(status_value: str, status_label: str) -> str:
        status_value = str(status_value or "").strip().lower()
        status_label = str(status_label or "").strip().lower()

        if status_value == "passed" or status_label == "aprobado":
            return "studentGradeStatusApproved"
        if status_value == "failed" or status_label == "reprobado":
            return "studentGradeStatusFailed"
        return "studentGradeStatusPending"

    @staticmethod
    def _format_grade(value) -> str:
        if value in (None, ""):
            return "—"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_average(value) -> str:
        if value in (None, ""):
            return "—"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    def get_styles(self) -> str:
        return """
        QWidget#studentGradeRecordRoot {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QLabel#studentGradePageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 900;
        }

        QLabel#studentGradePageSubtitle {
            color: #475569;
            font-size: 14px;
            font-weight: 600;
        }

        QPushButton#studentGradeSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 800;
        }

        QPushButton#studentGradeSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QFrame#studentGradeSummaryPanel,
        QFrame#studentGradeControlsPanel,
        QFrame#studentGradeTablePanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QFrame#studentGradeSummaryCard {
            background-color: #f8fbff;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QLabel#studentGradeSummaryValue {
            color: #1e3a8a;
            font-size: 22px;
            font-weight: 950;
        }

        QLabel#studentGradeSummaryTitle {
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#studentGradeInfoLabel {
            background-color: #eff6ff;
            color: #1e3a8a;
            border: 1px solid #bfdbfe;
            border-radius: 14px;
            padding: 12px 16px;
            font-size: 13px;
            font-weight: 700;
        }

        QLineEdit#studentGradeSearchInput {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 14px;
            font-weight: 600;
        }

        QLineEdit#studentGradeSearchInput:focus {
            border-color: #2563eb;
            background-color: #f8fbff;
        }

        QLabel#studentGradeVisibleCount {
            color: #475569;
            font-size: 13px;
            font-weight: 800;
        }

        QTableWidget#studentGradeTable {
            background-color: white;
            alternate-background-color: #f8fbff;
            color: #1e293b;
            border: none;
            gridline-color: #e2e8f0;
            selection-background-color: #dbeafe;
            selection-color: #0f172a;
            font-size: 13px;
            font-weight: 600;
        }

        QTableWidget#studentGradeTable QLabel {
            color: inherit;
        }

        QTableWidget#studentGradeTable::item {
            padding: 8px;
        }

        QHeaderView::section {
            background-color: #1e3a8a;
            color: white;
            border: none;
            border-right: 1px solid #3153a3;
            padding: 10px 8px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#studentGradeStatusApproved {
            background-color: #dcfce7;
            color: #166534;
            border: 1px solid #86efac;
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#studentGradeStatusFailed {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#studentGradeStatusPending {
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#studentGradeEmptyLabel {
            background-color: white;
            color: #64748b;
            border: 1px dashed #cbd5e1;
            border-radius: 18px;
            padding: 42px;
            font-size: 17px;
            font-weight: 800;
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
