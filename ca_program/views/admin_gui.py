from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ca_program.views.admin_dashboard_widget import AdminDashboardWidget
from ca_program.views.course_manager_gui import CourseManagerWidget
from ca_program.views.professor_manager_gui import ProfessorManagerWidget
from ca_program.views.student_manager_gui import StudentManagerWidget


class AdminGUI(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.nav_buttons: dict[str, QPushButton] = {}
        self.views: dict[str, QWidget] = {}

        self.setWindowTitle("Cambridge Academy | Administración")
        self.setMinimumSize(1280, 760)
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.change_view("dashboard")

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.views = {
            "dashboard": AdminDashboardWidget(navigate=self.change_view),
            "students": StudentManagerWidget(),
            "courses": CourseManagerWidget(),
            "professors": ProfessorManagerWidget(),
        }

        for view in self.views.values():
            self.stack.addWidget(view)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)

        self.statusBar().showMessage("Panel administrativo listo")

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(10)

        brand = QLabel("CA")
        brand.setObjectName("brandBadge")
        brand.setAlignment(Qt.AlignCenter)

        title = QLabel("Administración")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignCenter)

        user_name = getattr(self.user, "name", "Administrador")
        subtitle = QLabel(user_name)
        subtitle.setObjectName("sidebarSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(brand, alignment=Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self._add_nav_button(layout, "dashboard", "Inicio")
        self._add_nav_button(layout, "students", "Estudiantes")
        self._add_nav_button(layout, "courses", "Cursos")
        self._add_nav_button(layout, "professors", "Profesores")

        layout.addStretch()

        logout_btn = QPushButton("Cerrar sesión")
        logout_btn.setObjectName("logoutButton")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _add_nav_button(self, layout: QVBoxLayout, key: str, text: str):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setObjectName("navButton")
        button.clicked.connect(lambda checked=False, view_key=key: self.change_view(view_key))
        self.nav_buttons[key] = button
        layout.addWidget(button)

    def change_view(self, view_name: str):
        view = self.views.get(view_name)
        if view is None:
            return

        self.stack.setCurrentWidget(view)
        for key, button in self.nav_buttons.items():
            button.setChecked(key == view_name)

        labels = {
            "dashboard": "Inicio",
            "students": "Gestión de estudiantes",
            "courses": "Gestión de cursos",
            "professors": "Gestión de profesores",
        }
        self.statusBar().showMessage(labels.get(view_name, "Panel administrativo"))

    def logout(self):
        from ca_program.views.login_gui import LoginGUI

        self.login_window = LoginGUI()
        self.login_window.show()
        self.close()

    def get_styles(self) -> str:
        return """
        QMainWindow, QWidget#root {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#sidebar {
            background-color: #1e3a8a;
            border: none;
        }

        QLabel#brandBadge {
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

        QLabel#sidebarTitle {
            color: white;
            font-size: 20px;
            font-weight: 700;
            padding-top: 8px;
        }

        QLabel#sidebarSubtitle {
            color: #c7d2fe;
            font-size: 13px;
            padding-bottom: 8px;
        }

        QPushButton#navButton {
            background-color: transparent;
            color: #dbeafe;
            text-align: left;
            border: none;
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 600;
        }

        QPushButton#navButton:hover {
            background-color: rgba(255, 255, 255, 0.12);
            color: white;
        }

        QPushButton#navButton:checked {
            background-color: #2563eb;
            color: white;
        }

        QPushButton#logoutButton {
            background-color: #16a34a;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QPushButton#logoutButton:hover {
            background-color: #15803d;
        }

        QLabel#pageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 800;
        }

        QLabel#pageSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QFrame#card {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QLabel#cardTitle {
            color: #0f172a;
            font-size: 18px;
            font-weight: 700;
        }

        QLabel#cardText {
            color: #475569;
            line-height: 1.4;
        }

        QLabel#tagLabel {
            background-color: #dcfce7;
            color: #166534;
            padding: 4px 8px;
            border-radius: 8px;
            font-weight: 700;
        }

        QLabel#fieldLabel {
            color: #334155;
            font-size: 13px;
            font-weight: 700;
        }

        QLabel#serviceStatus[state="ok"] {
            color: #166534;
            background-color: #dcfce7;
            border: 1px solid #bbf7d0;
            border-radius: 10px;
            padding: 8px 12px;
        }

        QLabel#serviceStatus[state="warning"] {
            color: #854d0e;
            background-color: #fef3c7;
            border: 1px solid #fde68a;
            border-radius: 10px;
            padding: 8px 12px;
        }

        QLabel#selectionStatus, QLabel#tableHint {
            color: #475569;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 8px 10px;
            font-size: 13px;
        }

        QScrollArea#formScrollArea {
            background-color: transparent;
            border: none;
        }

        QWidget#formScrollContent {
            background-color: transparent;
        }

        QLineEdit, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
            background-color: white;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
            selection-background-color: #2563eb;
        }

        QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #2563eb;
        }

        QPushButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 700;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }

        QPushButton#secondaryButton {
            background-color: #eff6ff;
            color: #1e3a8a;
            border: 1px solid #bfdbfe;
        }

        QPushButton#secondaryButton:hover {
            background-color: #dbeafe;
        }

        QTableWidget {
            background-color: white;
            alternate-background-color: #f8fafc;
            gridline-color: #e2e8f0;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            selection-background-color: #dbeafe;
            selection-color: #0f172a;
            color: #0f172a;
            font-size: 13px;
        }

        QHeaderView::section {
            background-color: #1e3a8a;
            color: white;
            border: none;
            padding: 7px;
            font-weight: 700;
            font-size: 12px;
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

        QStatusBar {
            background-color: #f8fafc;
            color: #475569;
        }
        """
