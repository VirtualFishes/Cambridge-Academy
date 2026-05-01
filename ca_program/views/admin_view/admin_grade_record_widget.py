"""Vista administrativa de consulta del registro académico.

Permite buscar estudiantes y visualizar sus notas confirmadas. Es una pantalla
de solo lectura: no registra, modifica ni elimina calificaciones.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.grade_service import GradeService
from ca_program.views.admin_view.admin_view_utils import make_table_item, safe_text


class AdminGradeRecordWidget(QWidget):
    """Vista administrativa para consultar el registro académico por estudiante.

    HU-17: permite que el usuario administrativo busque un estudiante y consulte
    su planilla de notas. Esta vista es estrictamente de consulta: no registra,
    no modifica y no elimina calificaciones.
    """

    STUDENT_COL_ID = 0
    STUDENT_COL_NAME = 1

    GRADE_COL_CODE = 0
    GRADE_COL_COURSE = 1
    GRADE_COL_PROFESSOR = 2
    GRADE_COL_GRADE1 = 3
    GRADE_COL_GRADE2 = 4
    GRADE_COL_GRADE3 = 5
    GRADE_COL_AVERAGE = 6
    GRADE_COL_STATUS = 7

    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user
        self.students: list[dict] = []
        self.grade_records: list[dict] = []
        self.selected_student: dict | None = None
        self.summary: dict = {}

        self.setObjectName("adminGradeRecordRoot")
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.load_students(show_error=False)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("adminGradeHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        title_box = QWidget()
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("Registro académico")
        title.setObjectName("adminGradePageTitle")

        subtitle = QLabel(
            "Consulta las notas de los estudiantes con inscripciones confirmadas. "
            "Esta pantalla es de solo lectura para control académico administrativo."
        )
        subtitle.setObjectName("adminGradePageSubtitle")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("adminGradeSecondaryButton")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh_current_view)

        header_layout.addWidget(title_box, 1)
        header_layout.addWidget(refresh_button, 0, Qt.AlignTop)

        filters_panel = QFrame()
        filters_panel.setObjectName("adminGradeFiltersPanel")
        filters_layout = QHBoxLayout(filters_panel)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("adminGradeSearchInput")
        self.search_input.setPlaceholderText("Buscar estudiante por identificación, nombre o correo...")
        self.search_input.returnPressed.connect(self.load_students)

        search_button = QPushButton("Buscar")
        search_button.setObjectName("adminGradePrimaryButton")
        search_button.setCursor(Qt.PointingHandCursor)
        search_button.clicked.connect(self.load_students)

        clear_button = QPushButton("Limpiar")
        clear_button.setObjectName("adminGradeSecondaryButton")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.clear_search)

        filters_layout.addWidget(self.search_input, 1)
        filters_layout.addWidget(search_button, 0)
        filters_layout.addWidget(clear_button, 0)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        students_panel = QFrame()
        students_panel.setObjectName("adminGradeStudentsPanel")
        students_panel.setMinimumWidth(330)
        students_panel.setMaximumWidth(380)
        students_layout = QVBoxLayout(students_panel)
        students_layout.setContentsMargins(16, 16, 16, 16)
        students_layout.setSpacing(10)

        students_header = QHBoxLayout()
        students_title = QLabel("Estudiantes")
        students_title.setObjectName("adminGradeSectionTitle")
        self.students_count_label = QLabel("0 registros")
        self.students_count_label.setObjectName("adminGradeCounterLabel")
        self.students_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        students_header.addWidget(students_title, 1)
        students_header.addWidget(self.students_count_label, 0)

        self.students_table = QTableWidget(0, 2)
        self.students_table.setObjectName("adminGradeStudentsTable")
        self.students_table.setHorizontalHeaderLabels(["Documento", "Estudiante"])
        self.students_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.students_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.students_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.verticalHeader().setVisible(False)
        self.students_table.verticalHeader().setDefaultSectionSize(48)
        self.students_table.itemSelectionChanged.connect(self.handle_student_selection)

        students_header_view = self.students_table.horizontalHeader()
        students_header_view.setStretchLastSection(False)
        students_header_view.setSectionResizeMode(self.STUDENT_COL_ID, QHeaderView.ResizeToContents)
        students_header_view.setSectionResizeMode(self.STUDENT_COL_NAME, QHeaderView.Stretch)

        self.students_empty_label = QLabel("No hay estudiantes para mostrar.")
        self.students_empty_label.setObjectName("adminGradeEmptySmallLabel")
        self.students_empty_label.setAlignment(Qt.AlignCenter)
        self.students_empty_label.setWordWrap(True)
        self.students_empty_label.hide()

        students_layout.addLayout(students_header)
        students_layout.addWidget(self.students_table, 1)
        students_layout.addWidget(self.students_empty_label, 1)

        records_panel = QFrame()
        records_panel.setObjectName("adminGradeRecordsPanel")
        records_panel_layout = QVBoxLayout(records_panel)
        records_panel_layout.setContentsMargins(0, 0, 0, 0)
        records_panel_layout.setSpacing(0)

        self.records_scroll = QScrollArea()
        self.records_scroll.setObjectName("adminGradeRecordsScroll")
        self.records_scroll.setWidgetResizable(True)
        self.records_scroll.setFrameShape(QFrame.NoFrame)
        self.records_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        records_content = QWidget()
        records_content.setObjectName("adminGradeRecordsContent")
        records_layout = QVBoxLayout(records_content)
        records_layout.setContentsMargins(18, 18, 18, 18)
        records_layout.setSpacing(10)

        selected_card = QFrame()
        selected_card.setObjectName("adminGradeSelectedCard")
        selected_card.setMaximumHeight(82)
        selected_layout = QVBoxLayout(selected_card)
        selected_layout.setContentsMargins(16, 14, 16, 14)
        selected_layout.setSpacing(4)

        self.selected_name_label = QLabel("Selecciona un estudiante")
        self.selected_name_label.setObjectName("adminGradeSelectedName")
        self.selected_name_label.setWordWrap(True)

        self.selected_detail_label = QLabel("El registro académico aparecerá en esta sección.")
        self.selected_detail_label.setObjectName("adminGradeSelectedDetail")
        self.selected_detail_label.setWordWrap(True)

        selected_layout.addWidget(self.selected_name_label)
        selected_layout.addWidget(self.selected_detail_label)

        self.summary_grid = QGridLayout()
        self.summary_grid.setSpacing(12)

        self.card_confirmed = self._create_summary_card("Cursos confirmados", "0")
        self.card_graded = self._create_summary_card("Cursos calificados", "0")
        self.card_average = self._create_summary_card("Promedio general", "0.00")
        self.card_approved = self._create_summary_card("Aprobados", "0")
        self.card_failed = self._create_summary_card("Reprobados", "0")
        self.card_pending = self._create_summary_card("Pendientes", "0")

        summary_cards = [
            self.card_confirmed,
            self.card_graded,
            self.card_average,
            self.card_approved,
            self.card_failed,
            self.card_pending,
        ]
        for index, card in enumerate(summary_cards):
            self.summary_grid.addWidget(card["frame"], index // 3, index % 3)

        table_controls = QFrame()
        table_controls.setObjectName("adminGradeTableControls")
        table_controls.setMaximumHeight(62)
        table_controls_layout = QHBoxLayout(table_controls)
        table_controls_layout.setContentsMargins(14, 12, 14, 12)
        table_controls_layout.setSpacing(10)

        self.records_search_input = QLineEdit()
        self.records_search_input.setObjectName("adminGradeSearchInput")
        self.records_search_input.setPlaceholderText("Filtrar planilla por curso, profesor, código o estado...")
        self.records_search_input.textChanged.connect(self.apply_record_filter)

        self.records_count_label = QLabel("Registros visibles: 0")
        self.records_count_label.setObjectName("adminGradeCounterLabel")
        self.records_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        table_controls_layout.addWidget(self.records_search_input, 1)
        table_controls_layout.addWidget(self.records_count_label, 0)

        self.records_table = QTableWidget(0, 8)
        self.records_table.setObjectName("adminGradeRecordsTable")
        self.records_table.setHorizontalHeaderLabels([
            "Código",
            "Curso",
            "Profesor",
            "Nota 1",
            "Nota 2",
            "Nota 3",
            "Promedio",
            "Estado",
        ])
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.records_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.verticalHeader().setDefaultSectionSize(54)
        self.records_table.setWordWrap(True)
        self.records_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.records_table.setMinimumHeight(320)

        records_header = self.records_table.horizontalHeader()
        records_header.setStretchLastSection(False)
        records_header.setSectionResizeMode(self.GRADE_COL_CODE, QHeaderView.ResizeToContents)
        records_header.setSectionResizeMode(self.GRADE_COL_COURSE, QHeaderView.Stretch)
        records_header.setSectionResizeMode(self.GRADE_COL_PROFESSOR, QHeaderView.Stretch)
        records_header.setSectionResizeMode(self.GRADE_COL_GRADE1, QHeaderView.ResizeToContents)
        records_header.setSectionResizeMode(self.GRADE_COL_GRADE2, QHeaderView.ResizeToContents)
        records_header.setSectionResizeMode(self.GRADE_COL_GRADE3, QHeaderView.ResizeToContents)
        records_header.setSectionResizeMode(self.GRADE_COL_AVERAGE, QHeaderView.ResizeToContents)
        records_header.setSectionResizeMode(self.GRADE_COL_STATUS, QHeaderView.Fixed)
        self.records_table.setColumnWidth(self.GRADE_COL_STATUS, 128)

        self.records_empty_label = QLabel("Selecciona un estudiante para consultar su registro académico.")
        self.records_empty_label.setObjectName("adminGradeEmptyLabel")
        self.records_empty_label.setAlignment(Qt.AlignCenter)
        self.records_empty_label.setWordWrap(True)

        records_layout.addWidget(selected_card)
        records_layout.addLayout(self.summary_grid)
        records_layout.addWidget(table_controls)
        records_layout.addWidget(self.records_table, 1)
        records_layout.addWidget(self.records_empty_label, 1)

        self.records_scroll.setWidget(records_content)
        records_panel_layout.addWidget(self.records_scroll)

        content_layout.addWidget(students_panel, 0)
        content_layout.addWidget(records_panel, 1)

        root.addWidget(header)
        root.addWidget(filters_panel)
        root.addLayout(content_layout, 1)

        self.refresh_summary({})
        self.records_table.hide()
        table_controls.hide()
        self.table_controls = table_controls

    def _create_summary_card(self, label: str, value: str) -> dict:
        frame = QFrame()
        frame.setObjectName("adminGradeSummaryCard")
        frame.setMinimumHeight(66)
        frame.setMaximumHeight(76)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setObjectName("adminGradeSummaryValue")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setWordWrap(True)

        title_label = QLabel(label)
        title_label.setObjectName("adminGradeSummaryTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)

        layout.addWidget(value_label)
        layout.addWidget(title_label)

        return {"frame": frame, "value": value_label, "title": title_label}

    def set_user(self, user):
        self.user = user
        self.load_students(show_error=False)

    def refresh_current_view(self):
        selected_id = self._selected_student_id()
        self.load_students(show_error=False, keep_selected_id=selected_id)
        if selected_id:
            self.load_student_record(selected_id, show_error=False)

    def clear_search(self):
        self.search_input.clear()
        self.load_students(show_error=False)

    def load_students(self, show_error: bool = True, keep_selected_id: str | None = None):
        search_text = self.search_input.text().strip()
        result = GradeService.search_students_for_admin(search_text=search_text, user=self.user)

        if not result.get("success"):
            self.students = []
            self.render_students(empty_message="No fue posible consultar los estudiantes.")
            if show_error:
                QMessageBox.warning(
                    self,
                    "No fue posible consultar estudiantes",
                    result.get("message", "Ocurrió un error al consultar estudiantes."),
                )
            return

        raw_students = result.get("students") or result.get("data") or []
        self.students = [self.normalize_student(student) for student in raw_students]
        self.render_students(keep_selected_id=keep_selected_id)

    def render_students(self, empty_message: str | None = None, keep_selected_id: str | None = None):
        self.students_table.blockSignals(True)
        self.students_table.clearSelection()
        self.students_table.setRowCount(0)

        if not self.students:
            self.students_table.hide()
            self.students_empty_label.setText(empty_message or "No hay estudiantes que coincidan con la búsqueda.")
            self.students_empty_label.show()
            self.students_count_label.setText("0 registros")
            self.students_table.blockSignals(False)
            self.clear_selected_student()
            return

        self.students_empty_label.hide()
        self.students_table.show()
        self.students_table.setRowCount(len(self.students))

        selected_row = 0
        for row, student in enumerate(self.students):
            if keep_selected_id and str(student.get("id_student", "")) == str(keep_selected_id):
                selected_row = row

            self._set_student_item(row, self.STUDENT_COL_ID, student.get("id_student", ""), align=Qt.AlignCenter)
            name_item = self._set_student_item(row, self.STUDENT_COL_NAME, student.get("name", ""))
            if name_item:
                email = student.get("email") or "Sin correo registrado"
                name_item.setToolTip(f"Correo: {email}")

        self.students_count_label.setText(f"{len(self.students)} registros")
        self.students_table.blockSignals(False)
        self.students_table.selectRow(selected_row)
        QTimer.singleShot(0, lambda: self.students_table.scrollToTop())
        self.handle_student_selection()

    def _set_student_item(self, row: int, column: int, value, align=Qt.AlignLeft | Qt.AlignVCenter):
        item = make_table_item(value, align)
        if column == self.STUDENT_COL_ID:
            item.setData(Qt.UserRole, str(value or ""))
        self.students_table.setItem(row, column, item)
        return item

    def handle_student_selection(self):
        id_student = self._selected_student_id()
        if not id_student:
            self.clear_selected_student()
            return

        self.load_student_record(id_student)

    def _selected_student_id(self) -> str | None:
        selected_items = self.students_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        item = self.students_table.item(row, self.STUDENT_COL_ID)
        value = item.data(Qt.UserRole) if item else None
        return str(value).strip() if value not in (None, "") else None

    def clear_selected_student(self):
        self.selected_student = None
        self.grade_records = []
        self.summary = {}
        self.selected_name_label.setText("Selecciona un estudiante")
        self.selected_detail_label.setText("El registro académico aparecerá en esta sección.")
        self.refresh_summary({})
        self.render_grade_records(empty_message="Selecciona un estudiante para consultar su registro académico.")

    def load_student_record(self, id_student: str, show_error: bool = True):
        result = GradeService.get_student_grade_record_for_admin(id_student=id_student, user=self.user)

        if not result.get("success"):
            self.grade_records = []
            self.summary = result.get("summary") or {}
            self.selected_student = self._find_student_by_id(id_student)
            self.update_selected_student_header()
            self.refresh_summary(self.summary)
            self.render_grade_records(empty_message="No fue posible consultar el registro académico del estudiante.")
            if show_error:
                QMessageBox.warning(
                    self,
                    "No fue posible consultar el registro académico",
                    result.get("message", "Ocurrió un error al consultar el registro académico."),
                )
            return

        self.selected_student = self.normalize_student(
            result.get("student_data") or result.get("student") or self._find_student_by_id(id_student)
        )
        raw_records = result.get("grades") or result.get("grade_records") or result.get("data") or []
        self.grade_records = [self.normalize_grade_record(record) for record in raw_records]
        self.summary = result.get("summary") or {}

        self.update_selected_student_header()
        self.refresh_summary(self.summary)
        self.render_grade_records()

    def update_selected_student_header(self):
        student = self.selected_student or {}
        name = safe_text(student.get("name"), "Estudiante seleccionado")
        id_student = safe_text(student.get("id_student"))
        email = safe_text(student.get("email"), "Sin correo registrado")

        self.selected_name_label.setText(name)
        self.selected_detail_label.setText(f"Documento: {id_student}  |  Correo: {email}")

    def render_grade_records(self, empty_message: str | None = None):
        self.records_table.setRowCount(0)
        self.records_search_input.blockSignals(True)
        self.records_search_input.clear()
        self.records_search_input.blockSignals(False)

        if not self.grade_records:
            self.records_table.hide()
            self.table_controls.hide()
            self.records_empty_label.setText(
                empty_message
                or "El estudiante seleccionado no tiene cursos confirmados con registro académico disponible."
            )
            self.records_empty_label.show()
            self.records_count_label.setText("Registros visibles: 0")
            return

        self.records_empty_label.hide()
        self.table_controls.show()
        self.records_table.show()
        self.records_table.setRowCount(len(self.grade_records))

        for row, record in enumerate(self.grade_records):
            self._set_grade_item(row, self.GRADE_COL_CODE, record.get("code_course", ""), align=Qt.AlignCenter)
            self._set_grade_item(row, self.GRADE_COL_COURSE, record.get("course_name", ""))
            self._set_grade_item(row, self.GRADE_COL_PROFESSOR, record.get("professor_name", ""))
            self._set_grade_item(row, self.GRADE_COL_GRADE1, self.format_grade(record.get("grade1")), align=Qt.AlignCenter)
            self._set_grade_item(row, self.GRADE_COL_GRADE2, self.format_grade(record.get("grade2")), align=Qt.AlignCenter)
            self._set_grade_item(row, self.GRADE_COL_GRADE3, self.format_grade(record.get("grade3")), align=Qt.AlignCenter)
            self._set_grade_item(row, self.GRADE_COL_AVERAGE, self.format_average(record.get("average")), align=Qt.AlignCenter)
            self._set_status_badge(row, record)

            search_blob = " ".join([
                str(record.get("code_course", "")),
                str(record.get("course_name", "")),
                str(record.get("professor_name", "")),
                str(record.get("status_label", "")),
            ]).lower()
            item = self.records_table.item(row, self.GRADE_COL_CODE)
            if item:
                item.setData(Qt.UserRole, search_blob)

        self.apply_record_filter()
        QTimer.singleShot(0, lambda: self.records_table.scrollToTop())

    def _set_grade_item(self, row: int, column: int, value, align=Qt.AlignLeft | Qt.AlignVCenter):
        self.records_table.setItem(row, column, make_table_item(value, align))

    def _set_status_badge(self, row: int, record: dict):
        status_value = str(record.get("status", "pending") or "pending").strip().lower()
        status_label = self.status_to_label(status_value, record.get("status_label"))

        badge = QLabel(status_label)
        badge.setAlignment(Qt.AlignCenter)
        badge.setObjectName(self.status_badge_name(status_value, status_label))
        badge.setMinimumWidth(108)
        badge.setMinimumHeight(28)
        badge.setMargin(2)

        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        layout.addWidget(badge, 0, Qt.AlignCenter)

        status_item = QTableWidgetItem(status_label)
        status_item.setTextAlignment(Qt.AlignCenter)
        self.records_table.setItem(row, self.GRADE_COL_STATUS, status_item)
        self.records_table.setCellWidget(row, self.GRADE_COL_STATUS, wrapper)

    def apply_record_filter(self):
        query = self.records_search_input.text().strip().lower()
        visible = 0

        for row in range(self.records_table.rowCount()):
            item = self.records_table.item(row, self.GRADE_COL_CODE)
            search_blob = str(item.data(Qt.UserRole) if item else "").lower()
            should_show = not query or query in search_blob
            self.records_table.setRowHidden(row, not should_show)
            if should_show:
                visible += 1

        self.records_count_label.setText(f"Registros visibles: {visible}")

        if self.grade_records and visible == 0:
            self.records_empty_label.setText("No hay registros que coincidan con el filtro de la planilla.")
            self.records_empty_label.show()
        elif self.grade_records:
            self.records_empty_label.hide()

    def refresh_summary(self, summary: dict):
        confirmed = self.read_summary(summary, "confirmed_courses", "total_courses", "total_enrolled")
        graded = self.read_summary(summary, "graded_courses", "total_graded", "graded")
        average = self.read_summary(summary, "general_average", "academic_average")
        approved = self.read_summary(summary, "approved")
        failed = self.read_summary(summary, "failed")
        pending = self.read_summary(summary, "pending_courses", "pending")

        self.card_confirmed["value"].setText(str(confirmed or 0))
        self.card_graded["value"].setText(str(graded or 0))
        self.card_average["value"].setText(self.format_average(average))
        self.card_approved["value"].setText(str(approved or 0))
        self.card_failed["value"].setText(str(failed or 0))
        self.card_pending["value"].setText(str(pending or 0))

    @staticmethod
    def read_summary(summary: dict, *keys):
        for key in keys:
            value = (summary or {}).get(key)
            if value not in (None, ""):
                return value
        return 0

    def _find_student_by_id(self, id_student: str) -> dict:
        for student in self.students:
            if str(student.get("id_student", "")) == str(id_student):
                return student
        return {"id_student": id_student}

    @staticmethod
    def normalize_student(student) -> dict:
        if isinstance(student, dict):
            return {
                "id_student": student.get("id_student", ""),
                "id_user": student.get("id_user", ""),
                "name": student.get("name", ""),
                "email": student.get("email", ""),
                "birth_date": student.get("birth_date", ""),
                "nationality": student.get("nationality", ""),
            }

        user = getattr(student, "user", None)
        return {
            "id_student": getattr(student, "id_student", ""),
            "id_user": getattr(user, "id_user", ""),
            "name": getattr(user, "name", ""),
            "email": getattr(user, "email", ""),
            "birth_date": getattr(user, "birth_date", ""),
            "nationality": getattr(user, "nationality", ""),
        }

    @staticmethod
    def normalize_grade_record(record: dict) -> dict:
        if not isinstance(record, dict):
            return {}

        course = record.get("course") or {}
        professor = record.get("professor") or course.get("professor") or {}

        has_grade = bool(record.get("has_grade"))
        status = str(record.get("status", "pending") or "pending").strip().lower()
        if not has_grade:
            status = "pending"

        status_label = AdminGradeRecordWidget.status_to_label(status, record.get("status_label"))

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
    def status_to_label(status: str, current_label=None) -> str:
        status_value = str(status or "pending").strip().lower()
        current = str(current_label or "").strip().lower()

        if status_value == "passed" or current == "aprobado":
            return "Aprobado"
        if status_value == "failed" or current == "reprobado":
            return "Reprobado"
        return "Pendiente"

    @staticmethod
    def status_badge_name(status_value: str, status_label: str) -> str:
        status_value = str(status_value or "").strip().lower()
        status_label = str(status_label or "").strip().lower()

        if status_value == "passed" or status_label == "aprobado":
            return "adminGradeStatusApproved"
        if status_value == "failed" or status_label == "reprobado":
            return "adminGradeStatusFailed"
        return "adminGradeStatusPending"

    @staticmethod
    def format_grade(value) -> str:
        if value in (None, ""):
            return "—"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def format_average(value) -> str:
        if value in (None, ""):
            return "—"
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    def get_styles(self) -> str:
        return """
        QWidget#adminGradeRecordRoot {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QLabel#adminGradePageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 900;
        }

        QLabel#adminGradePageSubtitle {
            color: #475569;
            font-size: 14px;
            font-weight: 600;
        }

        QFrame#adminGradeFiltersPanel,
        QFrame#adminGradeStudentsPanel,
        QFrame#adminGradeRecordsPanel,
        QFrame#adminGradeTableControls,
        QFrame#adminGradeSelectedCard {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QWidget#adminGradeRecordsContent {
            background-color: white;
        }

        QFrame#adminGradeSummaryCard {
            background-color: #f8fbff;
            border: 1px solid #dbe4f0;
            border-radius: 14px;
        }

        QLabel#adminGradeSectionTitle {
            color: #1e3a8a;
            font-size: 18px;
            font-weight: 900;
        }

        QLabel#adminGradeCounterLabel {
            color: #475569;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#adminGradeSelectedName {
            color: #1e3a8a;
            font-size: 18px;
            font-weight: 900;
        }

        QLabel#adminGradeSelectedDetail {
            color: #475569;
            font-size: 13px;
            font-weight: 700;
        }

        QLabel#adminGradeSummaryValue {
            color: #1e3a8a;
            font-size: 20px;
            font-weight: 950;
        }

        QLabel#adminGradeSummaryTitle {
            color: #64748b;
            font-size: 11px;
            font-weight: 800;
        }

        QLineEdit#adminGradeSearchInput {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 14px;
            font-weight: 600;
        }

        QLineEdit#adminGradeSearchInput:focus {
            border-color: #2563eb;
            background-color: #f8fbff;
        }

        QPushButton#adminGradePrimaryButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 900;
        }

        QPushButton#adminGradePrimaryButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton#adminGradeSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 800;
        }

        QPushButton#adminGradeSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QTableWidget#adminGradeStudentsTable,
        QTableWidget#adminGradeRecordsTable {
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

        QTableWidget#adminGradeStudentsTable::item,
        QTableWidget#adminGradeRecordsTable::item {
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

        QLabel#adminGradeStatusApproved {
            background-color: #dcfce7;
            color: #166534;
            border: 1px solid #86efac;
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#adminGradeStatusFailed {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#adminGradeStatusPending {
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
            border-radius: 10px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 900;
        }

        QLabel#adminGradeEmptyLabel,
        QLabel#adminGradeEmptySmallLabel {
            background-color: white;
            color: #64748b;
            border: 1px dashed #cbd5e1;
            border-radius: 18px;
            padding: 34px;
            font-size: 16px;
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
