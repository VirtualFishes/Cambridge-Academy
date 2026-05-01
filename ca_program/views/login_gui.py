from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ca_program.services.login_service import LoginService


class LoginGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cambridge Academy | Inicio de sesión")
        self.setFixedSize(400, 300)
        self.setStyleSheet(self.get_styles())
        self.login_service = LoginService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Iniciar sesión")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre de usuario")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Ingresar")
        login_btn.clicked.connect(self.handle_login)

        layout.addWidget(title)
        layout.addSpacing(15)
        layout.addWidget(self.name_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def handle_login(self):
        name = self.name_input.text().strip()
        password = self.password_input.text().strip()

        if not name or not password:
            QMessageBox.warning(self, "Campos obligatorios", "Ingresa el usuario y la contraseña.")
            return

        result = self.login_service.login(name, password)

        if not result["success"]:
            QMessageBox.warning(self, "No fue posible ingresar", result["message"])
            return

        user = result["user"]

        if user.role.name == "ADMIN":
            self.open_admin(user)
        elif user.role.name == "STUDENT":
            self.open_student(user)
        else:
            QMessageBox.information(
                self,
                "Acceso no disponible",
                "Este perfil aún no tiene un panel implementado.",
            )

    def open_admin(self, user=None):
        from ca_program.views.admin_view.admin_gui import AdminGUI

        self.admin_window = AdminGUI(user=user)
        self.admin_window.show()
        self.close()

    def open_student(self, user=None):
        from ca_program.views.student_view.student_gui import StudentGUI

        self.student_window = StudentGUI(user=user)
        self.student_window.show()
        self.close()

    def get_styles(self):
        return """
        QWidget {
            background-color: #e1e7f0;
            font-size: 14px;
        }

        QLabel#title {
            font-size: 22px;
            font-weight: bold;
            color: #1e3a8a;
        }

        QLineEdit {
            color: #0f172a;
            background-color: white;
            padding: 8px;
            border: 1px solid #cbd5f5;
            border-radius: 6px;
        }

        QLineEdit:focus {
            border: 1px solid #2563eb;
        }

        QPushButton {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 6px;
            font-weight: 700;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }
        """
