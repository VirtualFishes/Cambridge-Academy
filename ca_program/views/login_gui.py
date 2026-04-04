"""
Vista de Login del sistema ca_program.
Interfaz gráfica construida con PySide6.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPixmap, QColor, QPalette, QIcon

from ca_program.services.auth_service import AuthService
from ca_program.services.login_service import LoginService


# ──────────────────────────────────────────────────────────────────────────────
# Paleta de colores
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {
    "bg":           "#0d0d0d",
    "card":         "#161616",
    "border":       "#2a2a2a",
    "accent":       "#4f8ef7",
    "accent_hover": "#3a72d8",
    "text":         "#f0f0f0",
    "subtext":      "#888888",
    "error":        "#e05c5c",
    "input_bg":     "#1e1e1e",
    "input_border": "#333333",
}

STYLESHEET = f"""
QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}}

QFrame#card {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
}}

QLabel#title {{
    color: {COLORS['text']};
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#subtitle {{
    color: {COLORS['subtext']};
    font-size: 13px;
}}

QLabel#field_label {{
    color: {COLORS['subtext']};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

QLabel#error_label {{
    color: {COLORS['error']};
    font-size: 12px;
    padding: 4px 0px;
}}

QLineEdit {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['input_border']};
    border-radius: 8px;
    padding: 10px 14px;
    color: {COLORS['text']};
    font-size: 14px;
    selection-background-color: {COLORS['accent']};
}}

QLineEdit:focus {{
    border: 1px solid {COLORS['accent']};
}}

QPushButton#btn_login {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

QPushButton#btn_login:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#btn_login:pressed {{
    background-color: #2e5bbf;
}}

QPushButton#btn_login:disabled {{
    background-color: #2a2a2a;
    color: {COLORS['subtext']};
}}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Ventana principal de Login
# ──────────────────────────────────────────────────────────────────────────────

class LoginGUI(QWidget):
    """Vista gráfica del formulario de inicio de sesión."""

    def __init__(self, auth_service: AuthService = None):
        super().__init__()

        self._auth_service = auth_service or AuthService()
        self._login_service = LoginService(self._auth_service)

        self._setup_window()
        self._build_ui()

    # ── Configuración de ventana ─────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("Iniciar sesión")
        self.setFixedSize(440, 520)
        self.setStyleSheet(STYLESHEET)
        self._center_window()

    def _center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # ── Construcción de UI ───────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        card = self._build_card()
        root.addWidget(card, alignment=Qt.AlignCenter)

    def _build_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(380)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 40, 36, 40)
        layout.setSpacing(0)

        # Encabezado
        title = QLabel("Bienvenido")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignLeft)

        subtitle = QLabel("Ingresa tus credenciales para continuar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignLeft)

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(subtitle)
        layout.addSpacing(32)

        # Campo: Usuario
        layout.addWidget(self._field_label("USUARIO"))
        layout.addSpacing(6)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre de usuario")
        self.input_name.returnPressed.connect(self._handle_login)
        layout.addWidget(self.input_name)
        layout.addSpacing(18)

        # Campo: Contraseña
        layout.addWidget(self._field_label("CONTRASEÑA"))
        layout.addSpacing(6)
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.returnPressed.connect(self._handle_login)
        layout.addWidget(self.input_password)
        layout.addSpacing(10)

        # Mensaje de error
        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("error_label")
        self.lbl_error.setAlignment(Qt.AlignLeft)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)
        layout.addSpacing(24)

        # Botón login
        self.btn_login = QPushButton("Iniciar sesión")
        self.btn_login.setObjectName("btn_login")
        self.btn_login.setFixedHeight(46)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.clicked.connect(self._handle_login)
        layout.addWidget(self.btn_login)

        return card

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("field_label")
        return label

    # ── Lógica de login ──────────────────────────────────────────────────────

    def _handle_login(self):
        self._clear_error()
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Verificando...")

        name = self.input_name.text()
        password = self.input_password.text()

        success, message, user = self._login_service.login(name, password)

        self.btn_login.setEnabled(True)
        self.btn_login.setText("Iniciar sesión")

        if not success:
            self._show_error(message)
            return

        self._on_login_success(user)

    def _on_login_success(self, user):
        """Cierra la ventana y redirige según el rol del usuario."""
        redirect = self._login_service.get_redirect_view(user)
        self.hide()

        if redirect == "admin":
            from ca_program.views.admin_gui import AdminGUI
            self._next_window = AdminGUI(self._auth_service)
            self._next_window.show()
        else:
            # Placeholder para vistas de profesor/estudiante
            placeholder = QWidget()
            placeholder.setWindowTitle(f"Panel — {user.name} ({user.role})")
            placeholder.resize(800, 600)
            placeholder.setStyleSheet(f"background:{COLORS['bg']};")
            lbl = QLabel(f"Bienvenido, {user.name}\nRol: {user.role}", placeholder)
            lbl.setStyleSheet(f"color:{COLORS['text']}; font-size:20px;")
            lbl.move(200, 250)
            self._next_window = placeholder
            self._next_window.show()

    def _show_error(self, message: str):
        self.lbl_error.setText(message)
        self.lbl_error.show()

    def _clear_error(self):
        self.lbl_error.hide()
        self.lbl_error.setText("")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point independiente
# ──────────────────────────────────────────────────────────────────────────────

def run():
    app = QApplication(sys.argv)
    window = LoginGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
