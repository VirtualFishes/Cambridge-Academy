import importlib

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.account_service import AccountService
from ca_program.services.professor_service import ProfessorService
from ca_program.views.change_password_dialog import ChangePasswordDialog
from ca_program.views.professor_view.professor_course_detail_widget import ProfessorCourseDetailWidget
from ca_program.views.professor_view.grade_registration_widget import GradeRegistrationWidget
from ca_program.views.professor_view.grade_record_widget import GradeRecordWidget


class ProfessorGUI(QMainWindow):
    """Panel principal para usuarios con rol profesor."""

    ASSIGNED_COURSES_VIEW = "assigned_courses"
    COURSE_DETAIL_VIEW = "course_detail"
    GRADE_REGISTRATION_VIEW = "grade_registration"
    GRADE_RECORD_VIEW = "grade_record"

    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.nav_buttons: dict[str, QPushButton] = {}
        self.views: dict[str, QWidget] = {}

        self.setWindowTitle("Cambridge Academy | Profesor")
        self.setMinimumSize(1180, 720)
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.change_view(self.ASSIGNED_COURSES_VIEW)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("professorRoot")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        self.stack = QStackedWidget()
        self.stack.setObjectName("professorContentStack")
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.assigned_courses_view = AssignedCoursesWidget(
            self.user,
            on_view_course_detail=self.open_course_detail,
        )
        self.course_detail_view = ProfessorCourseDetailWidget(
            on_back=self.back_to_assigned_courses,
            on_register_grades=self.open_grade_registration,
            on_view_grade_record=self.open_grade_record,
        )
        self.grade_registration_view = GradeRegistrationWidget(
            user=self.user,
            on_back=self.back_to_course_detail,
        )
        self.grade_record_view = GradeRecordWidget(
            user=self.user,
            on_back=self.back_to_course_detail,
        )

        self.views = {
            self.ASSIGNED_COURSES_VIEW: self.assigned_courses_view,
            self.COURSE_DETAIL_VIEW: self.course_detail_view,
            self.GRADE_REGISTRATION_VIEW: self.grade_registration_view,
            self.GRADE_RECORD_VIEW: self.grade_record_view,
        }

        for view in self.views.values():
            self.stack.addWidget(view)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)

        self.statusBar().showMessage("Panel de profesor listo")

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("professorSidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(10)

        brand = QLabel("CA")
        brand.setObjectName("professorBrandBadge")
        brand.setAlignment(Qt.AlignCenter)

        title = QLabel("Profesor")
        title.setObjectName("professorSidebarTitle")
        title.setAlignment(Qt.AlignCenter)

        user_name = getattr(self.user, "name", "Profesor")
        subtitle = QLabel(user_name)
        subtitle.setObjectName("professorSidebarSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(brand, alignment=Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self._add_nav_button(layout, self.ASSIGNED_COURSES_VIEW, "Cursos asignados")

        layout.addStretch()

        self._add_action_button(layout, "Cambiar contraseña", self.open_change_password_dialog)

        logout_btn = QPushButton("Cerrar sesión")
        logout_btn.setObjectName("professorLogoutButton")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _add_nav_button(self, layout: QVBoxLayout, key: str, text: str):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setObjectName("professorNavButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda checked=False, view_key=key: self.change_view(view_key))
        self.nav_buttons[key] = button
        layout.addWidget(button)

    def _add_action_button(self, layout: QVBoxLayout, text: str, callback):
        button = QPushButton(text)
        button.setObjectName("professorSecurityButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        layout.addWidget(button)

    def change_view(self, view_name: str):
        view = self.views.get(view_name)
        if view is None:
            return

        self.stack.setCurrentWidget(view)

        if view_name == self.ASSIGNED_COURSES_VIEW and hasattr(view, "load_courses"):
            view.load_courses(show_error=False)
        elif view_name == self.GRADE_REGISTRATION_VIEW and hasattr(view, "load_students"):
            view.load_students(show_error=False)
        elif view_name == self.GRADE_RECORD_VIEW and hasattr(view, "load_records"):
            view.load_records(show_error=False)

        for key, button in self.nav_buttons.items():
            button.setChecked(key == view_name)

        labels = {
            self.ASSIGNED_COURSES_VIEW: "Cursos asignados",
            self.COURSE_DETAIL_VIEW: "Detalle del curso",
            self.GRADE_REGISTRATION_VIEW: "Registro de notas",
            self.GRADE_RECORD_VIEW: "Planilla de notas",
        }
        self.statusBar().showMessage(labels.get(view_name, "Panel de profesor"))

    def open_course_detail(self, course: dict | None):
        """Abre la vista de detalle de un curso asignado al profesor autenticado."""
        code_course = self._extract_course_code(course)

        if not code_course:
            QMessageBox.warning(
                self,
                "Curso no identificado",
                "No fue posible identificar el curso seleccionado.",
            )
            return

        result = ProfessorService.get_assigned_course_detail_by_user(
            user=self.user,
            code_course=code_course,
        )

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible consultar el curso",
                result.get("message", "Ocurrió un error al consultar el detalle del curso."),
            )
            return

        course_detail = result.get("course") or result.get("data") or {}
        self.current_course_detail = course_detail
        self.course_detail_view.set_course(course_detail)
        self.change_view(self.COURSE_DETAIL_VIEW)

    def open_grade_registration(self, course: dict | None = None):
        """Abre la vista de registro de notas para el curso asignado seleccionado."""
        selected_course = course or getattr(self, "current_course_detail", None) or {}
        code_course = self._extract_course_code(selected_course)

        if not code_course:
            QMessageBox.warning(
                self,
                "Curso no identificado",
                "No fue posible identificar el curso para registrar notas.",
            )
            return

        self.grade_registration_view.set_context(
            user=self.user,
            course=selected_course,
        )
        self.change_view(self.GRADE_REGISTRATION_VIEW)

    def open_grade_record(self, course: dict | None = None):
        """Abre la planilla de consulta de notas para el curso asignado seleccionado."""
        selected_course = course or getattr(self, "current_course_detail", None) or {}
        code_course = self._extract_course_code(selected_course)

        if not code_course:
            QMessageBox.warning(
                self,
                "Curso no identificado",
                "No fue posible identificar el curso para consultar notas.",
            )
            return

        self.grade_record_view.set_context(
            user=self.user,
            course=selected_course,
        )
        self.change_view(self.GRADE_RECORD_VIEW)

    def back_to_course_detail(self):
        """Regresa desde el registro o consulta de notas al detalle del curso."""
        self.change_view(self.COURSE_DETAIL_VIEW)

    def back_to_assigned_courses(self):
        """Regresa desde el detalle del curso a la lista de cursos asignados."""
        self.change_view(self.ASSIGNED_COURSES_VIEW)

    @staticmethod
    def _extract_course_code(course: dict | None) -> str:
        if not isinstance(course, dict):
            return ""

        for key in ("code_course", "course_code", "code"):
            value = course.get(key)
            if value not in (None, ""):
                return str(value).strip()

        return ""

    def open_change_password_dialog(self):
        """Abre el diálogo de cambio de contraseña para el profesor autenticado."""
        id_user = self._get_user_id()

        if not id_user:
            QMessageBox.warning(
                self,
                "Usuario no identificado",
                "No fue posible identificar el usuario autenticado.",
            )
            return

        dialog = ChangePasswordDialog(parent=self)

        if dialog.exec() != QDialog.Accepted:
            return

        password_data = dialog.get_password_data()
        result = AccountService.change_password(
            id_user=id_user,
            current_password=password_data.get("current_password"),
            new_password=password_data.get("new_password"),
            confirm_password=password_data.get("confirm_password"),
        )

        if result.get("success"):
            QMessageBox.information(
                self,
                "Contraseña actualizada",
                result.get("message", "Contraseña actualizada correctamente."),
            )
        else:
            QMessageBox.warning(
                self,
                "No fue posible cambiar la contraseña",
                result.get("message", "Ocurrió un error al cambiar la contraseña."),
            )

    def logout(self):
        LoginWindow = self._get_login_window_class()
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def _get_user_id(self):
        return getattr(self.user, "id_user", None)

    @staticmethod
    def _get_login_window_class():
        """Obtiene la ventana de inicio de sesión según la estructura vigente."""
        try:
            login_module = importlib.import_module("ca_program.views.login_view")
        except ModuleNotFoundError:
            login_module = importlib.import_module("ca_program.views.login_gui")

        login_window = getattr(login_module, "LoginGUI", None)
        if login_window is not None:
            return login_window

        login_window = getattr(login_module, "LoginView", None)
        if login_window is not None:
            return login_window

        raise ImportError("No se encontró LoginGUI ni LoginView en el módulo de login.")

    def get_styles(self) -> str:
        return """
        QMainWindow, QWidget#professorRoot {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#professorSidebar {
            background-color: #1e3a8a;
            border: none;
        }

        QLabel#professorBrandBadge {
            background-color: #16a34a;
            color: white;
            border-radius: 28px;
            min-width: 56px;
            min-height: 56px;
            max-width: 56px;
            max-height: 56px;
            font-size: 22px;
            font-weight: 800;
        }

        QLabel#professorSidebarTitle {
            color: white;
            font-size: 20px;
            font-weight: 700;
            padding-top: 8px;
        }

        QLabel#professorSidebarSubtitle {
            color: #c7d2fe;
            font-size: 13px;
            padding-bottom: 8px;
        }

        QPushButton#professorNavButton {
            background-color: transparent;
            color: #dbeafe;
            text-align: left;
            border: none;
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 600;
        }

        QPushButton#professorNavButton:hover {
            background-color: rgba(255, 255, 255, 0.12);
            color: white;
        }

        QPushButton#professorNavButton:checked {
            background-color: #2563eb;
            color: white;
        }

        QPushButton#professorSecurityButton {
            background-color: rgba(255, 255, 255, 0.10);
            color: #dbeafe;
            text-align: left;
            border: 1px solid rgba(191, 219, 254, 0.35);
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QPushButton#professorSecurityButton:hover {
            background-color: rgba(255, 255, 255, 0.18);
            color: white;
            border-color: rgba(255, 255, 255, 0.55);
        }

        QPushButton#professorLogoutButton {
            background-color: #16a34a;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QPushButton#professorLogoutButton:hover {
            background-color: #15803d;
        }

        QWidget#professorContentStack, QWidget#professorScrollContent {
            background-color: #eaf0f8;
        }

        QLabel#professorPageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 800;
        }

        QLabel#professorPageSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QPushButton#professorSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 700;
        }

        QPushButton#professorSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QFrame#professorCoursesPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QScrollArea#professorScrollArea {
            background-color: transparent;
            border: none;
        }

        QFrame#professorCourseCard {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QFrame#professorCourseCard:hover {
            border: 1px solid #93c5fd;
            background-color: #f8fbff;
        }

        QLabel#professorCourseTitle {
            color: #0f172a;
            font-size: 18px;
            font-weight: 800;
        }

        QLabel#professorCourseTag {
            background-color: #dcfce7;
            color: #166534;
            padding: 5px 9px;
            border-radius: 9px;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#professorCourseCode {
            color: #1e3a8a;
            font-size: 13px;
            font-weight: 800;
        }

        QLabel#professorCourseInfo {
            color: #475569;
            font-size: 13px;
            font-weight: 600;
        }

        QLabel#professorCourseMetric {
            background-color: #f8fbff;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 8px 10px;
            font-size: 13px;
            font-weight: 700;
        }

        QPushButton#professorCourseDetailButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 800;
        }

        QPushButton#professorCourseDetailButton:hover {
            background-color: #1d4ed8;
        }

        QLabel#professorEmptyState {
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


class AssignedCoursesWidget(QWidget):
    """Vista de cursos asignados para profesores."""

    def __init__(self, user=None, on_view_course_detail=None):
        super().__init__()
        self.user = user
        self.on_view_course_detail = on_view_course_detail
        self.courses: list[dict] = []
        self.current_columns = 0
        self.empty_message_override: str | None = None

        self._build_ui()
        self.load_courses(show_error=False)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("professorHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("Cursos asignados")
        title.setObjectName("professorPageTitle")

        subtitle = QLabel("Consulta el resumen de los cursos que tienes asignados.")
        subtitle.setObjectName("professorPageSubtitle")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("professorSecondaryButton")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.load_courses)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(refresh_button, 0, Qt.AlignTop)

        self.courses_panel = QFrame()
        self.courses_panel.setObjectName("professorCoursesPanel")
        panel_layout = QVBoxLayout(self.courses_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("professorScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("professorScrollContent")
        self.scroll_content.setMinimumHeight(430)

        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(22, 22, 22, 22)
        self.grid_layout.setHorizontalSpacing(18)
        self.grid_layout.setVerticalSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.scroll_content)
        panel_layout.addWidget(self.scroll_area)

        main_layout.addWidget(header)
        main_layout.addWidget(self.courses_panel, 1)

    def load_courses(self, show_error: bool = True):
        result = ProfessorService.get_assigned_courses_by_user(user=self.user)

        if not result.get("success"):
            if show_error:
                QMessageBox.warning(
                    self,
                    "No fue posible consultar los cursos asignados",
                    result.get("message", "Ocurrió un error al consultar los cursos asignados."),
                )

            self.courses = []
            self._schedule_populate_grid(
                result.get("message", "No fue posible consultar los cursos asignados.")
            )
            return

        self.courses = result.get("courses", []) or result.get("data", []) or []
        self._schedule_populate_grid()

    def _schedule_populate_grid(self, custom_empty_message: str | None = None):
        self.empty_message_override = custom_empty_message
        QTimer.singleShot(0, self._populate_grid)

    def _populate_grid(self):
        self._clear_grid()
        self._reset_grid_stretches()

        columns = self._calculate_columns()
        self.current_columns = columns

        if not self.courses:
            self.grid_layout.setAlignment(Qt.AlignCenter)
            message = self.empty_message_override or "Aún no tienes cursos asignados para mostrar."
            empty_message = QLabel(message)
            empty_message.setObjectName("professorEmptyState")
            empty_message.setAlignment(Qt.AlignCenter)
            empty_message.setWordWrap(True)
            self.grid_layout.addWidget(empty_message, 0, 0, 1, columns, Qt.AlignCenter)
            return

        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        for index, course in enumerate(self.courses):
            row = index // columns
            column = index % columns
            card = ProfessorCourseCardWidget(
                course,
                on_view_detail=self._handle_view_course_detail,
            )
            self.grid_layout.addWidget(card, row, column, Qt.AlignTop | Qt.AlignLeft)

        self._add_grid_spacers(columns)

    def _handle_view_course_detail(self, course: dict):
        if callable(self.on_view_course_detail):
            self.on_view_course_detail(course)

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _reset_grid_stretches(self):
        rows_to_reset = max(12, (len(self.courses) // 3) + 4)
        for row in range(rows_to_reset):
            self.grid_layout.setRowStretch(row, 0)

        for column in range(4):
            self.grid_layout.setColumnStretch(column, 0)

    def _add_grid_spacers(self, columns: int):
        for column in range(columns):
            self.grid_layout.setColumnStretch(column, 0)

        self.grid_layout.setColumnStretch(columns, 1)

        last_row = ((len(self.courses) - 1) // columns) + 1
        self.grid_layout.setRowStretch(last_row, 1)

    def _calculate_columns(self) -> int:
        width = max(
            self.courses_panel.width() if hasattr(self, "courses_panel") else 0,
            self.scroll_area.viewport().width() if hasattr(self, "scroll_area") else 0,
            self.width(),
        )

        if width >= 980:
            return 3
        if width >= 650:
            return 2
        return 1

    def showEvent(self, event):
        super().showEvent(event)
        self._schedule_populate_grid(self.empty_message_override)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not hasattr(self, "grid_layout"):
            return

        new_columns = self._calculate_columns()
        if self.current_columns and new_columns != self.current_columns:
            self._schedule_populate_grid(self.empty_message_override)


class ProfessorCourseCardWidget(QFrame):
    """Tarjeta de resumen para un curso asignado al profesor."""

    def __init__(self, course: dict, on_view_detail=None):
        super().__init__()
        self.course = course or {}
        self.on_view_detail = on_view_detail

        self.setObjectName("professorCourseCard")
        self.setMinimumWidth(300)
        self.setMaximumWidth(360)
        self.setMinimumHeight(292)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel(self._get_course_name())
        title.setObjectName("professorCourseTitle")
        title.setWordWrap(True)

        tag = QLabel("Asignado")
        tag.setObjectName("professorCourseTag")
        tag.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title, 1)
        header_layout.addWidget(tag, 0, Qt.AlignTop)

        code = QLabel(f"Código: {self._get_value('code_course', 'No registrado')}")
        code.setObjectName("professorCourseCode")
        code.setWordWrap(True)

        schedule = QLabel(f"Horario: {self._get_value('schedule', 'No registrado')}")
        schedule.setObjectName("professorCourseInfo")
        schedule.setWordWrap(True)

        location = QLabel(f"Ubicación: {self._get_value('location', 'No registrada')}")
        location.setObjectName("professorCourseInfo")
        location.setWordWrap(True)

        dates = QLabel(
            "Fechas: "
            f"{self._format_date(self.course.get('start_date'))} - "
            f"{self._format_date(self.course.get('end_date'))}"
        )
        dates.setObjectName("professorCourseInfo")
        dates.setWordWrap(True)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(8)

        students = QLabel(f"Estudiantes: {self._get_students_count()}")
        students.setObjectName("professorCourseMetric")
        students.setAlignment(Qt.AlignCenter)

        intensity = QLabel(f"Intensidad: {self._get_hours()} h")
        intensity.setObjectName("professorCourseMetric")
        intensity.setAlignment(Qt.AlignCenter)

        metrics_layout.addWidget(students)
        metrics_layout.addWidget(intensity)

        detail_button = QPushButton("Ver detalle")
        detail_button.setObjectName("professorCourseDetailButton")
        detail_button.setCursor(Qt.PointingHandCursor)
        detail_button.clicked.connect(self._handle_view_detail)

        layout.addLayout(header_layout)
        layout.addWidget(code)
        layout.addWidget(schedule)
        layout.addWidget(location)
        layout.addWidget(dates)
        layout.addStretch()
        layout.addLayout(metrics_layout)
        layout.addWidget(detail_button)

    def _handle_view_detail(self):
        if callable(self.on_view_detail):
            self.on_view_detail(self.course)

    def _get_course_name(self) -> str:
        name = str(self.course.get("name", "")).strip()
        return name or "Curso sin nombre"

    def _get_value(self, key: str, default: str) -> str:
        value = self.course.get(key)
        value = str(value).strip() if value not in (None, "") else ""
        return value or default

    def _get_students_count(self):
        value = self.course.get("enrolled_students", self.course.get("students", 0))
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _get_hours(self):
        value = self.course.get("intensity_hours", 0)
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0

        if number.is_integer():
            return int(number)
        return number

    @staticmethod
    def _format_date(value) -> str:
        text = str(value or "").strip()
        return text or "No registrada"
