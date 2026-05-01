from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
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
from ca_program.views.professor_view.grade_edit_dialog import GradeEditDialog


class GradeRecordWidget(QWidget):
    """Planilla académica de notas de un curso asignado.

    Integra la consulta del registro de notas y la corrección controlada de
    calificaciones existentes. La actualización se delega en GradeService para
    conservar validaciones de profesor, curso, matrícula y rango de notas.
    """

    COL_ENROLLMENT = 0
    COL_STUDENT = 1
    COL_EMAIL = 2
    COL_GRADE1 = 3
    COL_GRADE2 = 4
    COL_GRADE3 = 5
    COL_AVERAGE = 6
    COL_STATUS = 7
    COL_ACTION = 8

    def __init__(
        self,
        user=None,
        course: dict | None = None,
        on_back: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.user = user
        self.course = course or {}
        self.on_back = on_back
        self.grade_records: list[dict] = []
        self.summary: dict = {}

        self.setObjectName("gradeRecordRoot")
        self.setStyleSheet(self.get_styles())

        self._build_ui()

        if self.course:
            self.load_records(show_error=False)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("gradeRecordHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = QLabel("Registro de notas")
        self.page_title.setObjectName("gradeRecordPageTitle")
        self.page_title.setWordWrap(True)

        self.page_subtitle = QLabel("Consulta la planilla académica del curso seleccionado.")
        self.page_subtitle.setObjectName("gradeRecordPageSubtitle")
        self.page_subtitle.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)

        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setObjectName("gradeRecordSecondaryButton")
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.load_records)

        self.back_button = QPushButton("Volver")
        self.back_button.setObjectName("gradeRecordSecondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._handle_back)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(self.refresh_button, 0, Qt.AlignTop)
        header_layout.addWidget(self.back_button, 0, Qt.AlignTop)

        self.course_panel = QFrame()
        self.course_panel.setObjectName("gradeRecordCoursePanel")
        course_layout = QHBoxLayout(self.course_panel)
        course_layout.setContentsMargins(18, 16, 18, 16)
        course_layout.setSpacing(14)

        self.course_label = QLabel("Curso: No seleccionado")
        self.course_label.setObjectName("gradeRecordCourseText")
        self.course_label.setWordWrap(True)

        self.code_label = QLabel("Código: No registrado")
        self.code_label.setObjectName("gradeRecordCourseText")
        self.code_label.setWordWrap(True)

        self.total_label = QLabel("Estudiantes confirmados: 0")
        self.total_label.setObjectName("gradeRecordCourseText")
        self.total_label.setWordWrap(True)

        course_layout.addWidget(self.course_label, 2)
        course_layout.addWidget(self.code_label, 1)
        course_layout.addWidget(self.total_label, 1)

        self.cards_panel = QFrame()
        self.cards_panel.setObjectName("gradeRecordCardsPanel")
        cards_layout = QHBoxLayout(self.cards_panel)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        self.card_graded = self._create_summary_card("Calificados", "0")
        self.card_average = self._create_summary_card("Promedio general", "0.00")
        self.card_approved = self._create_summary_card("Aprobados", "0")
        self.card_failed = self._create_summary_card("Reprobados", "0")
        self.card_pending = self._create_summary_card("Pendientes", "0")

        cards_layout.addWidget(self.card_graded["frame"])
        cards_layout.addWidget(self.card_average["frame"])
        cards_layout.addWidget(self.card_approved["frame"])
        cards_layout.addWidget(self.card_failed["frame"])
        cards_layout.addWidget(self.card_pending["frame"])

        self.info_label = QLabel(
            "Planilla académica del curso. Puedes consultar las calificaciones "
            "registradas y corregirlas desde el botón Editar de cada estudiante."
        )
        self.info_label.setObjectName("gradeRecordInfoLabel")
        self.info_label.setWordWrap(True)

        controls_panel = QFrame()
        controls_panel.setObjectName("gradeRecordControlsPanel")
        controls_layout = QHBoxLayout(controls_panel)
        controls_layout.setContentsMargins(16, 14, 16, 14)
        controls_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("gradeRecordSearchInput")
        self.search_input.setPlaceholderText("Buscar por estudiante, correo, matrícula o estado")
        self.search_input.textChanged.connect(self._apply_filter)

        self.visible_count_label = QLabel("Registros visibles: 0")
        self.visible_count_label.setObjectName("gradeRecordVisibleCount")

        controls_layout.addWidget(self.search_input, 1)
        controls_layout.addWidget(self.visible_count_label, 0)

        self.table_panel = QFrame()
        self.table_panel.setObjectName("gradeRecordTablePanel")
        table_layout = QVBoxLayout(self.table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.table = QTableWidget(0, 9)
        self.table.setObjectName("gradeRecordTable")
        self.table.setHorizontalHeaderLabels([
            "Matrícula",
            "Estudiante",
            "Correo",
            "Nota 1",
            "Nota 2",
            "Nota 3",
            "Promedio",
            "Estado",
            "Acción",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.setWordWrap(True)

        header_view = self.table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(self.COL_ENROLLMENT, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_STUDENT, QHeaderView.Stretch)
        header_view.setSectionResizeMode(self.COL_EMAIL, QHeaderView.Stretch)
        header_view.setSectionResizeMode(self.COL_GRADE1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_GRADE2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_GRADE3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_AVERAGE, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(self.COL_ACTION, QHeaderView.ResizeToContents)

        table_layout.addWidget(self.table)

        self.empty_label = QLabel("No hay notas registradas para este curso.")
        self.empty_label.setObjectName("gradeRecordEmptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()

        main_layout.addWidget(header)
        main_layout.addWidget(self.course_panel)
        main_layout.addWidget(self.cards_panel)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(controls_panel)
        main_layout.addWidget(self.table_panel, 1)
        main_layout.addWidget(self.empty_label, 1)

        self._refresh_course_header()
        self._refresh_summary({})

    def _create_summary_card(self, label: str, value: str) -> dict:
        frame = QFrame()
        frame.setObjectName("gradeRecordSummaryCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("gradeRecordSummaryValue")
        value_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(label)
        title_label.setObjectName("gradeRecordSummaryTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)

        layout.addWidget(value_label)
        layout.addWidget(title_label)

        return {
            "frame": frame,
            "value": value_label,
            "title": title_label,
        }

    def set_context(self, user=None, course: dict | None = None):
        if user is not None:
            self.user = user

        if course is not None:
            self.course = course or {}

        self._refresh_course_header()
        self.load_records(show_error=False)

    def set_user(self, user):
        self.user = user

    def set_course(self, course: dict | None):
        self.course = course or {}
        self._refresh_course_header()
        self.load_records(show_error=False)

    def set_back_callback(self, callback: Callable[[], None] | None):
        self.on_back = callback

    def load_records(self, show_error: bool = True):
        code_course = self._get_course_code()

        if not code_course:
            self.grade_records = []
            self.summary = {}
            self._refresh_summary({})
            self._populate_table("No fue posible identificar el curso seleccionado.")
            return

        result = GradeService.get_grade_record_by_course_for_user(
            user=self.user,
            code_course=code_course,
        )

        if not result.get("success"):
            self.grade_records = []
            self.summary = result.get("summary", {}) or {}
            self._refresh_summary(self.summary)
            if show_error:
                QMessageBox.warning(
                    self,
                    "No fue posible consultar el registro de notas",
                    result.get("message", "Ocurrió un error al consultar el registro de notas."),
                )
            self._populate_table(result.get("message", "No fue posible consultar el registro de notas."))
            return

        self.grade_records = result.get("grades", []) or result.get("grade_records", []) or result.get("data", []) or []
        self.summary = result.get("summary", {}) or {}
        self._refresh_summary(self.summary)
        self._populate_table()

    def _populate_table(self, custom_empty_message: str | None = None):
        self.table.setRowCount(0)
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)

        if not self.grade_records:
            self.table_panel.hide()
            self.empty_label.setText(custom_empty_message or "No hay notas registradas para este curso.")
            self.empty_label.show()
            self.visible_count_label.setText("Registros visibles: 0")
            return

        self.empty_label.hide()
        self.table_panel.show()
        self.table.setRowCount(len(self.grade_records))

        for row, record in enumerate(self.grade_records):
            self._populate_row(row, record)

        self.visible_count_label.setText(f"Registros visibles: {len(self.grade_records)}")
        QTimer.singleShot(0, self.table.resizeRowsToContents)

    def _populate_row(self, row: int, record: dict):
        id_enrollment = self._read_value(record, "id_enrollment", default="No registrado")
        student_name = self._read_value(record, "student_name", default="Estudiante sin nombre")
        student_email = self._read_value(record, "student_email", default="No registrado")
        grade1 = self._format_grade(record.get("grade1"))
        grade2 = self._format_grade(record.get("grade2"))
        grade3 = self._format_grade(record.get("grade3"))
        average = self._format_grade(record.get("average"))
        status = self._format_status(record.get("status_label") or record.get("status") or record.get("status_name"))

        self._set_text_item(row, self.COL_ENROLLMENT, id_enrollment, align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_STUDENT, student_name)
        self._set_text_item(row, self.COL_EMAIL, student_email)
        self._set_text_item(row, self.COL_GRADE1, grade1, align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_GRADE2, grade2, align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_GRADE3, grade3, align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_AVERAGE, average, align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_STATUS, status, align=Qt.AlignCenter)
        self._set_action_button(row, record)

    def _set_action_button(self, row: int, record: dict):
        button = QPushButton("Editar")
        button.setObjectName("gradeRecordEditButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumWidth(86)
        button.setMinimumHeight(34)
        button.setToolTip("Corregir notas del estudiante")
        button.clicked.connect(
            lambda checked=False, grade_record=dict(record): self._handle_edit_grade(grade_record)
        )
        self.table.setCellWidget(row, self.COL_ACTION, button)

    def _handle_edit_grade(self, record: dict):
        id_grade = self._read_value(record, "id_grade", default="")
        if not id_grade:
            QMessageBox.warning(
                self,
                "No fue posible editar",
                "El registro seleccionado no tiene identificador de nota.",
            )
            return

        code_course = self._get_course_code()
        if not code_course:
            QMessageBox.warning(
                self,
                "No fue posible editar",
                "No fue posible identificar el curso seleccionado.",
            )
            return

        dialog = GradeEditDialog(record, self)
        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.get_values()
        result = GradeService.update_grade_for_student(
            user=self.user,
            code_course=code_course,
            id_grade=values.get("id_grade"),
            grade1=values.get("grade1"),
            grade2=values.get("grade2"),
            grade3=values.get("grade3"),
        )

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible modificar las notas",
                result.get("message", "Ocurrió un error al modificar las notas."),
            )
            return

        QMessageBox.information(
            self,
            "Notas modificadas",
            result.get("message", "Notas modificadas correctamente."),
        )
        self.load_records(show_error=False)

    def _apply_filter(self):
        query = self.search_input.text().strip().lower()
        visible_rows = 0

        for row, record in enumerate(self.grade_records):
            searchable = " ".join([
                self._read_value(record, "id_enrollment"),
                self._read_value(record, "student_name"),
                self._read_value(record, "student_email"),
                self._read_value(record, "status"),
                self._read_value(record, "status_label"),
                self._read_value(record, "status_name"),
            ]).lower()
            should_show = not query or query in searchable
            self.table.setRowHidden(row, not should_show)
            if should_show:
                visible_rows += 1

        self.visible_count_label.setText(f"Registros visibles: {visible_rows}")

    def _refresh_course_header(self):
        course_name = self._read_course("name", default="No seleccionado")
        code_course = self._read_course("code_course", "course_code", default="No registrado")
        self.page_subtitle.setText(f"Curso: {course_name}")
        self.course_label.setText(f"Curso: {course_name}")
        self.code_label.setText(f"Código: {code_course}")

    def _refresh_summary(self, summary: dict):
        total_confirmed = self._read_summary_int(summary, "total_confirmed")
        total_graded = self._read_summary_int(summary, "total_graded", "graded")
        approved = self._read_summary_int(summary, "approved")
        failed = self._read_summary_int(summary, "failed")
        pending = self._read_summary_int(summary, "pending")
        course_average = self._read_summary_float(summary, "course_average")

        self.total_label.setText(f"Estudiantes confirmados: {total_confirmed}")
        self.card_graded["value"].setText(str(total_graded))
        self.card_average["value"].setText(f"{course_average:.2f}")
        self.card_approved["value"].setText(str(approved))
        self.card_failed["value"].setText(str(failed))
        self.card_pending["value"].setText(str(pending))

    def _handle_back(self):
        if callable(self.on_back):
            self.on_back()

    def _get_course_code(self) -> str:
        return self._read_course("code_course", "course_code", "code", default="").strip()

    def _read_course(self, *keys: str, default: str = "") -> str:
        if not isinstance(self.course, dict):
            return default

        for key in keys:
            value = self.course.get(key)
            if value not in (None, ""):
                return str(value).strip()
        return default

    @staticmethod
    def _read_value(record: dict, key: str, default: str = "") -> str:
        if not isinstance(record, dict):
            return default

        value = record.get(key)
        if value not in (None, ""):
            return str(value).strip()
        return default

    @staticmethod
    def _read_summary_int(summary: dict, *keys: str) -> int:
        if not isinstance(summary, dict):
            return 0

        for key in keys:
            value = summary.get(key)
            if value not in (None, ""):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return 0
        return 0

    @staticmethod
    def _read_summary_float(summary: dict, *keys: str) -> float:
        if not isinstance(summary, dict):
            return 0.0

        for key in keys:
            value = summary.get(key)
            if value not in (None, ""):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    @staticmethod
    def _format_grade(value) -> str:
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "0.00"

    @staticmethod
    def _format_status(status) -> str:
        clean_status = str(status or "").strip().lower()
        if clean_status in ("passed", "pass", "aprobado", "academicstatus.passed"):
            return "Aprobado"
        if clean_status in ("failed", "fail", "reprobado", "academicstatus.failed"):
            return "Reprobado"
        return str(status or "Sin estado").strip().capitalize()

    def _set_text_item(self, row: int, column: int, text, align=Qt.AlignVCenter | Qt.AlignLeft):
        item = QTableWidgetItem(str(text if text not in (None, "") else "No registrado"))
        item.setTextAlignment(align)
        flags = item.flags()
        item.setFlags(flags & ~Qt.ItemIsEditable)
        self.table.setItem(row, column, item)

    @staticmethod
    def get_styles() -> str:
        return """
        QWidget#gradeRecordRoot {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#gradeRecordHeader,
        QFrame#gradeRecordCardsPanel {
            background-color: transparent;
            border: none;
        }

        QLabel#gradeRecordPageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 800;
        }

        QLabel#gradeRecordPageSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QPushButton#gradeRecordSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 700;
        }

        QPushButton#gradeRecordSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QPushButton#gradeRecordEditButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 7px 12px;
            font-weight: 800;
        }

        QPushButton#gradeRecordEditButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton#gradeRecordEditButton:pressed {
            background-color: #1e40af;
        }

        QFrame#gradeRecordCoursePanel,
        QFrame#gradeRecordControlsPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QLabel#gradeRecordCourseText {
            color: #0f172a;
            font-weight: 800;
        }

        QFrame#gradeRecordSummaryCard {
            background-color: #f8fbff;
            border: 1px solid #dbeafe;
            border-radius: 16px;
        }

        QLabel#gradeRecordSummaryValue {
            color: #0f172a;
            font-size: 22px;
            font-weight: 900;
        }

        QLabel#gradeRecordSummaryTitle {
            color: #334155;
            font-size: 13px;
            font-weight: 800;
        }

        QLabel#gradeRecordInfoLabel {
            background-color: #dbeafe;
            color: #1e40af;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QLineEdit#gradeRecordSearchInput {
            background-color: white;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 12px;
        }

        QLineEdit#gradeRecordSearchInput:focus {
            border-color: #2563eb;
        }

        QLabel#gradeRecordVisibleCount {
            color: #475569;
            font-weight: 800;
        }

        QFrame#gradeRecordTablePanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QTableWidget#gradeRecordTable {
            background-color: white;
            alternate-background-color: #f8fbff;
            border: none;
            border-radius: 18px;
            gridline-color: #e2e8f0;
            color: #1e293b;
            selection-background-color: #dbeafe;
            selection-color: #0f172a;
        }

        QTableWidget#gradeRecordTable::item {
            padding: 8px;
        }

        QHeaderView::section {
            background-color: #1e3a8a;
            color: white;
            border: none;
            padding: 10px 8px;
            font-weight: 800;
        }

        QLabel#gradeRecordEmptyLabel {
            background-color: white;
            color: #64748b;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
            padding: 36px;
            font-size: 16px;
            font-weight: 600;
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
