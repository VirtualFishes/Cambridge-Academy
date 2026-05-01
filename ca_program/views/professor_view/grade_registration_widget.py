from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.grade_service import GradeService


class GradeRegistrationWidget(QWidget):
    """Vista de registro de notas para cursos asignados al profesor.

    Esta vista corresponde a la HU-26. Permite listar estudiantes con matrícula
    confirmada en un curso asignado al profesor autenticado y registrar sus tres
    notas académicas. La modificación de notas existentes queda bloqueada aquí,
    porque corresponde a la HU-28.
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
        self.students: list[dict] = []
        self.row_controls: dict[int, dict[str, object]] = {}

        self.setObjectName("gradeRegistrationRoot")
        self.setStyleSheet(self.get_styles())

        self._build_ui()

        if self.course:
            self.load_students(show_error=False)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("gradeRegistrationHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = QLabel("Registrar notas")
        self.page_title.setObjectName("gradeRegistrationPageTitle")
        self.page_title.setWordWrap(True)

        self.page_subtitle = QLabel("Selecciona las notas de cada estudiante y guarda el registro académico.")
        self.page_subtitle.setObjectName("gradeRegistrationPageSubtitle")
        self.page_subtitle.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)

        self.back_button = QPushButton("Volver")
        self.back_button.setObjectName("gradeRegistrationSecondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._handle_back)

        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setObjectName("gradeRegistrationSecondaryButton")
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.load_students)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(self.refresh_button, 0, Qt.AlignTop)
        header_layout.addWidget(self.back_button, 0, Qt.AlignTop)

        self.summary_panel = QFrame()
        self.summary_panel.setObjectName("gradeRegistrationSummaryPanel")
        summary_layout = QHBoxLayout(self.summary_panel)
        summary_layout.setContentsMargins(18, 16, 18, 16)
        summary_layout.setSpacing(14)

        self.course_label = QLabel("Curso: No seleccionado")
        self.course_label.setObjectName("gradeRegistrationSummaryText")
        self.course_label.setWordWrap(True)

        self.code_label = QLabel("Código: No registrado")
        self.code_label.setObjectName("gradeRegistrationSummaryText")
        self.code_label.setWordWrap(True)

        self.count_label = QLabel("Estudiantes: 0")
        self.count_label.setObjectName("gradeRegistrationSummaryText")
        self.count_label.setWordWrap(True)

        summary_layout.addWidget(self.course_label, 2)
        summary_layout.addWidget(self.code_label, 1)
        summary_layout.addWidget(self.count_label, 1)

        self.info_label = QLabel(
            "Solo se permite registrar notas a estudiantes con inscripción confirmada. "
            "Las notas ya registradas se muestran bloqueadas."
        )
        self.info_label.setObjectName("gradeRegistrationInfoLabel")
        self.info_label.setWordWrap(True)

        self.table_panel = QFrame()
        self.table_panel.setObjectName("gradeRegistrationTablePanel")
        table_layout = QVBoxLayout(self.table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.table = QTableWidget(0, 9)
        self.table.setObjectName("gradeRegistrationTable")
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
        self.table.verticalHeader().setDefaultSectionSize(58)
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

        self.empty_label = QLabel("No hay estudiantes disponibles para registrar notas.")
        self.empty_label.setObjectName("gradeRegistrationEmptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()

        main_layout.addWidget(header)
        main_layout.addWidget(self.summary_panel)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.table_panel, 1)
        main_layout.addWidget(self.empty_label, 1)

        self._refresh_course_header()

    def set_context(self, user=None, course: dict | None = None):
        """Actualiza usuario y curso, y recarga los estudiantes calificables."""
        if user is not None:
            self.user = user

        if course is not None:
            self.course = course or {}

        self._refresh_course_header()
        self.load_students(show_error=False)

    def set_user(self, user):
        self.user = user

    def set_course(self, course: dict | None):
        self.course = course or {}
        self._refresh_course_header()
        self.load_students(show_error=False)

    def set_back_callback(self, callback: Callable[[], None] | None):
        self.on_back = callback

    def load_students(self, show_error: bool = True):
        code_course = self._get_course_code()

        if not code_course:
            self.students = []
            self._populate_table("No fue posible identificar el curso seleccionado.")
            return

        result = GradeService.get_students_for_grade_registration(
            user=self.user,
            code_course=code_course,
        )

        if not result.get("success"):
            self.students = []
            if show_error:
                QMessageBox.warning(
                    self,
                    "No fue posible consultar estudiantes",
                    result.get("message", "Ocurrió un error al consultar los estudiantes."),
                )
            self._populate_table(result.get("message", "No fue posible consultar estudiantes."))
            return

        self.students = result.get("students", []) or result.get("data", []) or []
        self._populate_table()

    def _populate_table(self, custom_empty_message: str | None = None):
        self.table.setRowCount(0)
        self.row_controls.clear()
        self.count_label.setText(f"Estudiantes: {len(self.students)}")

        if not self.students:
            self.table_panel.hide()
            self.empty_label.setText(custom_empty_message or "No hay estudiantes disponibles para registrar notas.")
            self.empty_label.show()
            return

        self.empty_label.hide()
        self.table_panel.show()
        self.table.setRowCount(len(self.students))

        for row, record in enumerate(self.students):
            self._populate_row(row, record)

        QTimer.singleShot(0, self.table.resizeRowsToContents)

    def _populate_row(self, row: int, record: dict):
        student = record.get("student") if isinstance(record.get("student"), dict) else {}
        grade = record.get("grade") if isinstance(record.get("grade"), dict) else None
        has_grade = bool(record.get("has_grade")) and grade is not None

        id_enrollment = record.get("id_enrollment", "")
        student_name = self._read_nested(student, "name", default="Estudiante sin nombre")
        student_email = self._read_nested(student, "email", default="No registrado")

        self._set_text_item(row, self.COL_ENROLLMENT, id_enrollment, align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_STUDENT, student_name)
        self._set_text_item(row, self.COL_EMAIL, student_email)

        grade1_value = self._read_grade_value(grade, "grade1") if has_grade else 0.0
        grade2_value = self._read_grade_value(grade, "grade2") if has_grade else 0.0
        grade3_value = self._read_grade_value(grade, "grade3") if has_grade else 0.0

        grade1_spin = self._create_grade_spinbox(grade1_value, enabled=not has_grade)
        grade2_spin = self._create_grade_spinbox(grade2_value, enabled=not has_grade)
        grade3_spin = self._create_grade_spinbox(grade3_value, enabled=not has_grade)

        self.table.setCellWidget(row, self.COL_GRADE1, grade1_spin)
        self.table.setCellWidget(row, self.COL_GRADE2, grade2_spin)
        self.table.setCellWidget(row, self.COL_GRADE3, grade3_spin)

        average = self._calculate_average_from_values(
            grade1_spin.value(),
            grade2_spin.value(),
            grade3_spin.value(),
        )
        if has_grade:
            average = self._read_grade_value(grade, "average", default=average)

        status = self._get_status_from_average(average)
        if has_grade:
            status = self._format_status(grade.get("status", grade.get("status_name", status)))

        self._set_text_item(row, self.COL_AVERAGE, f"{average:.2f}", align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_STATUS, status, align=Qt.AlignCenter)

        action_button = QPushButton("Registrado" if has_grade else "Guardar notas")
        action_button.setObjectName("gradeRegistrationActionButton" if not has_grade else "gradeRegistrationDisabledButton")
        action_button.setCursor(Qt.PointingHandCursor if not has_grade else Qt.ArrowCursor)
        action_button.setEnabled(not has_grade)
        action_button.clicked.connect(lambda checked=False, row_index=row: self._save_row(row_index))
        self.table.setCellWidget(row, self.COL_ACTION, action_button)

        self.row_controls[row] = {
            "record": record,
            "grade1": grade1_spin,
            "grade2": grade2_spin,
            "grade3": grade3_spin,
            "button": action_button,
        }

        if not has_grade:
            grade1_spin.valueChanged.connect(lambda value, row_index=row: self._update_row_calculation(row_index))
            grade2_spin.valueChanged.connect(lambda value, row_index=row: self._update_row_calculation(row_index))
            grade3_spin.valueChanged.connect(lambda value, row_index=row: self._update_row_calculation(row_index))
            self._update_row_calculation(row)

    def _save_row(self, row: int):
        controls = self.row_controls.get(row)
        if not controls:
            return

        record = controls.get("record") if isinstance(controls.get("record"), dict) else {}
        id_enrollment = record.get("id_enrollment")
        code_course = self._get_course_code()

        if not id_enrollment or not code_course:
            QMessageBox.warning(
                self,
                "Registro incompleto",
                "No fue posible identificar la matrícula o el curso seleccionado.",
            )
            return

        grade1 = controls["grade1"].value()
        grade2 = controls["grade2"].value()
        grade3 = controls["grade3"].value()

        result = GradeService.register_grade_for_student(
            user=self.user,
            code_course=code_course,
            id_enrollment=id_enrollment,
            grade1=grade1,
            grade2=grade2,
            grade3=grade3,
        )

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible registrar las notas",
                result.get("message", "Ocurrió un error al registrar las notas."),
            )
            return

        QMessageBox.information(
            self,
            "Notas registradas",
            result.get("message", "Notas registradas correctamente."),
        )
        self.load_students(show_error=False)

    def _update_row_calculation(self, row: int):
        controls = self.row_controls.get(row)
        if not controls:
            return

        grade1 = controls["grade1"].value()
        grade2 = controls["grade2"].value()
        grade3 = controls["grade3"].value()
        average = self._calculate_average_from_values(grade1, grade2, grade3)
        status = self._get_status_from_average(average)

        self._set_text_item(row, self.COL_AVERAGE, f"{average:.2f}", align=Qt.AlignCenter)
        self._set_text_item(row, self.COL_STATUS, status, align=Qt.AlignCenter)

    def _refresh_course_header(self):
        course_name = self._read_course("name", default="No seleccionado")
        code_course = self._read_course("code_course", "course_code", default="No registrado")
        self.page_subtitle.setText(f"Curso: {course_name}")
        self.course_label.setText(f"Curso: {course_name}")
        self.code_label.setText(f"Código: {code_course}")

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
    def _read_nested(data: dict, *keys: str, default: str = "") -> str:
        if not isinstance(data, dict):
            return default

        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return str(value).strip()
        return default

    @staticmethod
    def _read_grade_value(grade: dict | None, key: str, default: float = 0.0) -> float:
        if not isinstance(grade, dict):
            return default

        value = grade.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _create_grade_spinbox(value: float = 0.0, enabled: bool = True) -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setObjectName("gradeRegistrationSpinBox")
        spinbox.setRange(GradeService.MIN_GRADE, GradeService.MAX_GRADE)
        spinbox.setDecimals(2)
        spinbox.setSingleStep(0.1)
        spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        spinbox.setValue(float(value or 0.0))
        spinbox.setEnabled(enabled)
        spinbox.setAlignment(Qt.AlignCenter)
        spinbox.setMinimumWidth(92)
        return spinbox

    @staticmethod
    def _calculate_average_from_values(grade1: float, grade2: float, grade3: float) -> float:
        return round((float(grade1) + float(grade2) + float(grade3)) / 3, 2)

    @staticmethod
    def _get_status_from_average(average: float) -> str:
        return "Aprobado" if float(average) >= GradeService.PASSING_GRADE else "Reprobado"

    @staticmethod
    def _format_status(status) -> str:
        clean_status = str(status or "").strip().lower()
        if clean_status in ("passed", "pass", "aprobado", "academicstatus.passed"):
            return "Aprobado"
        if clean_status in ("failed", "fail", "reprobado", "academicstatus.failed"):
            return "Reprobado"
        return clean_status.capitalize() if clean_status else "No registrado"

    def _set_text_item(self, row: int, column: int, text, align=Qt.AlignVCenter | Qt.AlignLeft):
        item = QTableWidgetItem(str(text if text not in (None, "") else "No registrado"))
        item.setTextAlignment(align)
        flags = item.flags()
        item.setFlags(flags & ~Qt.ItemIsEditable)
        self.table.setItem(row, column, item)

    @staticmethod
    def get_styles() -> str:
        return """
        QWidget#gradeRegistrationRoot {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#gradeRegistrationHeader {
            background-color: transparent;
            border: none;
        }

        QLabel#gradeRegistrationPageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 800;
        }

        QLabel#gradeRegistrationPageSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QPushButton#gradeRegistrationSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 700;
        }

        QPushButton#gradeRegistrationSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QFrame#gradeRegistrationSummaryPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QLabel#gradeRegistrationSummaryText {
            color: #0f172a;
            font-weight: 800;
        }

        QLabel#gradeRegistrationInfoLabel {
            background-color: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QFrame#gradeRegistrationTablePanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QTableWidget#gradeRegistrationTable {
            background-color: white;
            alternate-background-color: #f8fbff;
            border: none;
            border-radius: 18px;
            gridline-color: #e2e8f0;
            color: #1e293b;
            selection-background-color: #dbeafe;
            selection-color: #0f172a;
        }

        QTableWidget#gradeRegistrationTable::item {
            padding: 8px;
        }

        QHeaderView::section {
            background-color: #1e3a8a;
            color: white;
            border: none;
            padding: 10px 8px;
            font-weight: 800;
        }

        QDoubleSpinBox#gradeRegistrationSpinBox {
            background-color: white;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 6px 8px;
            font-weight: 700;
        }

        QDoubleSpinBox#gradeRegistrationSpinBox:focus {
            border-color: #2563eb;
        }

        QDoubleSpinBox#gradeRegistrationSpinBox::up-button,
        QDoubleSpinBox#gradeRegistrationSpinBox::down-button {
            width: 0px;
            height: 0px;
            border: none;
            background: transparent;
        }

        QDoubleSpinBox#gradeRegistrationSpinBox::up-arrow,
        QDoubleSpinBox#gradeRegistrationSpinBox::down-arrow {
            width: 0px;
            height: 0px;
            image: none;
        }

        QDoubleSpinBox#gradeRegistrationSpinBox:disabled {
            background-color: #f1f5f9;
            color: #64748b;
        }

        QPushButton#gradeRegistrationActionButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 9px;
            padding: 8px 12px;
            font-weight: 800;
        }

        QPushButton#gradeRegistrationActionButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton#gradeRegistrationDisabledButton {
            background-color: #e2e8f0;
            color: #64748b;
            border: none;
            border-radius: 9px;
            padding: 8px 12px;
            font-weight: 800;
        }

        QLabel#gradeRegistrationEmptyLabel {
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
