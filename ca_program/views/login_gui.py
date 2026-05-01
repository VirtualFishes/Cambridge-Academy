"""
Ventana de inicio de sesión de Cambridge Academy.

Este componente pertenece a la capa View. Captura credenciales, invoca al
servicio de autenticación y redirige al panel correspondiente según el rol del
usuario autenticado. No consulta modelos ni base de datos directamente.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ca_program.services.login_service import LoginService
from ca_program.views.view_utils import clean_text, get_user_role_name, show_critical, show_information, show_warning


class LoginGUI(QWidget):
    """
    Formulario principal de autenticación.

    La clase mantiene una responsabilidad concreta: presentar el formulario de
    acceso y abrir la vista inicial del rol autenticado. La validación profunda
    de credenciales permanece en LoginService.
    """

    WINDOW_TITLE = "Cambridge Academy | Inicio de sesión"
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 300

    ROLE_ADMIN = "ADMIN"
    ROLE_STUDENT = "STUDENT"
    ROLE_PROFESSOR = "PROFESSOR"

    def __init__(self, login_service: LoginService | None = None):
        super().__init__()

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setStyleSheet(self.get_styles())

        self.login_service = login_service or LoginService()
        self.name_input = None
        self.password_input = None
        self.login_button = None
        self.active_window = None

        self.init_ui()
        self._connect_events()

    def init_ui(self) -> None:
        """Construye el formulario visual de inicio de sesión."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Iniciar sesión")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre de usuario")
        self.name_input.setMinimumHeight(38)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(38)

        self.login_button = QPushButton("Ingresar")
        self.login_button.setDefault(True)

        layout.addWidget(title)
        layout.addSpacing(15)
        layout.addWidget(self.name_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        layout.addWidget(self.login_button)

    def _connect_events(self) -> None:
        """Conecta señales del formulario con sus acciones de interfaz."""
        self.login_button.clicked.connect(self.handle_login)
        self.name_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self) -> None:
        """
        Envía las credenciales al servicio y abre el panel correspondiente.

        El método mantiene la vista defensiva ante respuestas incompletas del
        servicio, mostrando mensajes comprensibles para el usuario final.
        """
        name = clean_text(self.name_input.text())
        password = clean_text(self.password_input.text())

        if not name or not password:
            show_warning(
                self,
                "Campos obligatorios",
                "Ingresa el usuario y la contraseña.",
            )
            return

        result = self.login_service.login(name, password)
        if not result.get("success"):
            show_warning(
                self,
                "No fue posible ingresar",
                result.get("message", "Credenciales no válidas."),
            )
            return

        user = result.get("user")
        if user is None:
            show_critical(
                self,
                "Respuesta incompleta",
                "El inicio de sesión fue aceptado, pero no se recibió el usuario autenticado.",
            )
            return

        self._open_panel_for_user(user)

    def _open_panel_for_user(self, user) -> None:
        """Abre la ventana principal asociada al rol autenticado."""
        role_name = get_user_role_name(user)

        if role_name == self.ROLE_ADMIN:
            self.open_admin(user)
            return

        if role_name == self.ROLE_STUDENT:
            self.open_student(user)
            return

        if role_name == self.ROLE_PROFESSOR:
            self.open_professor(user)
            return

        show_information(
            self,
            "Acceso no disponible",
            "Este perfil aún no tiene un panel implementado.",
        )

    def open_admin(self, user=None) -> None:
        """Abre el panel administrativo para usuarios con rol administrador."""
        from ca_program.views.admin_view.admin_gui import AdminGUI

        self._show_main_window(AdminGUI(user=user))

    def open_student(self, user=None) -> None:
        """Abre el panel estudiantil para usuarios con rol estudiante."""
        from ca_program.views.student_view.student_gui import StudentGUI

        self._show_main_window(StudentGUI(user=user))

    def open_professor(self, user=None) -> None:
        """Abre el panel docente para usuarios con rol profesor."""
        from ca_program.views.professor_view.professor_gui import ProfessorGUI

        self._show_main_window(ProfessorGUI(user=user))

    def _show_main_window(self, window: QWidget) -> None:
        """
        Muestra la ventana principal y conserva su referencia.

        En Qt es importante guardar la ventana abierta como atributo para evitar
        que el recolector de basura la destruya al salir del método.
        """
        self.active_window = window
        self.active_window.showMaximized()
        self.close()

    def get_styles(self) -> str:
        """Retorna la hoja de estilos de la ventana de inicio de sesión."""
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
