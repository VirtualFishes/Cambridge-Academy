from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QHBoxLayout
)
from PySide6.QtCore import Qt


class AdminGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel de Administrador")
        self.setMinimumSize(900, 600)

        self.setStyleSheet(self.get_styles())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Sidebar (menú lateral)
        self.sidebar = self.create_sidebar()

        # Área de contenido dinámico
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_home_view())

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.stack)

    def create_sidebar(self):
        sidebar = QWidget()
        layout = QVBoxLayout()
        sidebar.setLayout(layout)
        sidebar.setFixedWidth(220)

        title = QLabel("Administrador")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        btn_students = QPushButton("Estudiantes")
        btn_courses = QPushButton("Cursos")
        btn_professors = QPushButton("Profesores")
        btn_logout = QPushButton("Cerrar sesión")

        # Eventos (placeholder)
        btn_students.clicked.connect(lambda: self.change_view("students"))
        btn_courses.clicked.connect(lambda: self.change_view("courses"))
        btn_professors.clicked.connect(lambda: self.change_view("professors"))
        btn_logout.clicked.connect(self.logout)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(btn_students)
        layout.addWidget(btn_courses)
        layout.addWidget(btn_professors)
        layout.addStretch()
        layout.addWidget(btn_logout)

        return sidebar

    def create_home_view(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        label = QLabel("Bienvenido al panel de administración")
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("homeLabel")

        layout.addWidget(label)

        return widget

    def change_view(self, view_name):
        # Aquí luego integrarás los widgets reales (student_manager_gui, etc.)
        placeholder = QWidget()
        layout = QVBoxLayout()
        placeholder.setLayout(layout)

        label = QLabel(f"Vista de {view_name}")
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)

        self.stack.addWidget(placeholder)
        self.stack.setCurrentWidget(placeholder)

    def logout(self):
        from ca_program.views.login_gui import LoginGUI

        self.login_window = LoginGUI()
        self.login_window.show()
        self.close()

    def get_styles(self):
        return """
        /* Fondo general */
        QMainWindow {
            background-color: #e1e7f0;
        }

        /* Sidebar */
        QWidget {
            font-size: 14px;
        }

        QWidget > QWidget {
            background-color: #1e3a8a; /* Azul principal */
        }

        QLabel#title {
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
        }

        QPushButton {
            background-color: #2563eb; /* Azul */
            color: white;
            border: none;
            padding: 10px;
            margin: 5px 10px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }

        QPushButton:last-child {
            background-color: #16a34a; /* Verde secundario */
        }

        QPushButton:last-child:hover {
            background-color: #15803d;
        }

        QLabel#homeLabel {
            font-size: 20px;
            color: #1e293b;
        }
        """
