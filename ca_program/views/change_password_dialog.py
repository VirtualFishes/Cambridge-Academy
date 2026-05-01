"""
Diálogo de cambio de contraseña para usuarios autenticados.

Pertenece a la capa View dentro de MVC + Entities. Su responsabilidad es
mostrar el formulario, capturar los datos escritos por el usuario y exponerlos
a la vista contenedora. Las reglas de validación y actualización de contraseña
permanecen en AccountService.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ca_program.views.view_utils import (
    clean_text,
    create_password_input,
    set_password_fields_visible,
    wrap_labeled_field,
)


class ChangePasswordDialog(QDialog):
    """
    Formulario modal reutilizable para la HU-30: cambiar contraseña.

    El diálogo no conoce al usuario autenticado, no invoca servicios y no
    persiste información. Esto permite usarlo desde paneles administrativos,
    docentes o estudiantiles sin duplicar interfaz ni mezclar responsabilidades.
    """

    WINDOW_TITLE = "Cambiar contraseña"
    MINIMUM_WIDTH = 430

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setModal(True)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setObjectName("changePasswordDialog")
        self.setStyleSheet(self.get_styles())

        self.current_password_input = None
        self.new_password_input = None
        self.confirm_password_input = None
        self.show_passwords_check = None
        self.cancel_button = None
        self.save_button = None

        self._build_ui()
        self._connect_events()

    def _build_ui(self) -> None:
        """Construye los controles visuales del formulario."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(26, 24, 26, 24)
        main_layout.setSpacing(16)

        title = QLabel(self.WINDOW_TITLE)
        title.setObjectName("title")

        subtitle = QLabel("Actualiza tu contraseña para mantener segura tu cuenta.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        self.current_password_input = create_password_input("Contraseña actual")
        self.new_password_input = create_password_input("Nueva contraseña")
        self.confirm_password_input = create_password_input("Confirmar nueva contraseña")

        self.show_passwords_check = QCheckBox("Mostrar contraseñas")
        self.show_passwords_check.setObjectName("showPasswordsCheck")

        info_box = QLabel("La nueva contraseña debe ser distinta de la actual.")
        info_box.setObjectName("infoBox")
        info_box.setWordWrap(True)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(4)
        main_layout.addWidget(wrap_labeled_field("Contraseña actual", self.current_password_input))
        main_layout.addWidget(wrap_labeled_field("Nueva contraseña", self.new_password_input))
        main_layout.addWidget(wrap_labeled_field("Confirmar nueva contraseña", self.confirm_password_input))
        main_layout.addWidget(self.show_passwords_check)
        main_layout.addWidget(info_box)
        main_layout.addSpacing(4)
        main_layout.addLayout(self._build_buttons_layout())

    def _build_buttons_layout(self) -> QHBoxLayout:
        """Crea la fila inferior de acciones del diálogo."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("secondaryButton")

        self.save_button = QPushButton("Guardar cambios")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setDefault(True)

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        return buttons_layout

    def _connect_events(self) -> None:
        """Conecta señales visuales con acciones propias del diálogo."""
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)
        self.show_passwords_check.stateChanged.connect(self._toggle_password_visibility)

        for password_input in self._password_fields():
            password_input.returnPressed.connect(self.accept)

    def _password_fields(self) -> list:
        """Retorna los campos de contraseña administrados por el diálogo."""
        return [
            self.current_password_input,
            self.new_password_input,
            self.confirm_password_input,
        ]

    def _toggle_password_visibility(self) -> None:
        """Muestra u oculta todos los campos de contraseña del formulario."""
        set_password_fields_visible(
            fields=self._password_fields(),
            visible=self.show_passwords_check.isChecked(),
        )

    def get_password_data(self) -> dict:
        """
        Retorna los datos capturados por el formulario.

        La respuesta usa nombres compatibles con AccountService para que la
        vista contenedora pueda enviar el diccionario sin transformar claves.
        """
        return {
            "current_password": clean_text(self.current_password_input.text()),
            "new_password": clean_text(self.new_password_input.text()),
            "confirm_password": clean_text(self.confirm_password_input.text()),
        }

    def clear_fields(self) -> None:
        """Limpia el formulario para reutilizar el diálogo sin datos previos."""
        for password_input in self._password_fields():
            password_input.clear()

        self.show_passwords_check.setChecked(False)
        self.current_password_input.setFocus(Qt.PopupFocusReason)

    def showEvent(self, event) -> None:  # noqa: N802 - nombre definido por Qt.
        """Ubica el foco en el primer campo al mostrar el diálogo."""
        super().showEvent(event)
        self.current_password_input.setFocus(Qt.PopupFocusReason)

    def get_styles(self) -> str:
        """Retorna la hoja de estilos del diálogo."""
        return """
        QDialog#changePasswordDialog {
            background-color: #f8fafc;
        }

        QLabel#title {
            color: #1e3a8a;
            font-size: 22px;
            font-weight: bold;
        }

        QLabel#subtitle {
            color: #475569;
            font-size: 13px;
            margin-bottom: 4px;
        }

        QLabel#fieldLabel {
            color: #1e293b;
            font-size: 13px;
            font-weight: bold;
        }

        QLabel#infoBox {
            background-color: #e0f2fe;
            color: #075985;
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 10px;
            font-size: 12px;
        }

        QLineEdit {
            background-color: white;
            color: #111827;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 13px;
        }

        QLineEdit:focus {
            border: 1px solid #2563eb;
        }

        QCheckBox#showPasswordsCheck {
            color: #334155;
            font-size: 13px;
        }

        QPushButton {
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: bold;
            font-size: 13px;
        }

        QPushButton#primaryButton {
            background-color: #2563eb;
            color: white;
        }

        QPushButton#primaryButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton#secondaryButton {
            background-color: #e2e8f0;
            color: #1e293b;
        }

        QPushButton#secondaryButton:hover {
            background-color: #cbd5e1;
        }
        """
