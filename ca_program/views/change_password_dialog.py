from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QWidget,
)
from PySide6.QtCore import Qt


class ChangePasswordDialog(QDialog):
    """
    Diálogo reutilizable para la HU-30: cambiar contraseña.

    Este componente pertenece a la capa View. Solo captura los datos
    ingresados por el usuario y los entrega al componente que lo invoca.
    No valida reglas de negocio ni actualiza la base de datos directamente.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Cambiar contraseña")
        self.setModal(True)
        self.setMinimumWidth(430)
        self.setObjectName("changePasswordDialog")
        self.setStyleSheet(self.get_styles())

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(26, 24, 26, 24)
        main_layout.setSpacing(16)

        title = QLabel("Cambiar contraseña")
        title.setObjectName("title")

        subtitle = QLabel(
            "Actualiza tu contraseña para mantener segura tu cuenta."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        self.current_password_input = self._create_password_input(
            "Contraseña actual"
        )
        self.new_password_input = self._create_password_input(
            "Nueva contraseña"
        )
        self.confirm_password_input = self._create_password_input(
            "Confirmar nueva contraseña"
        )

        self.show_passwords_check = QCheckBox("Mostrar contraseñas")
        self.show_passwords_check.setObjectName("showPasswordsCheck")
        self.show_passwords_check.stateChanged.connect(
            self._toggle_password_visibility
        )

        info_box = QLabel(
            "La nueva contraseña debe ser distinta de la actual."
        )
        info_box.setObjectName("infoBox")
        info_box.setWordWrap(True)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("Guardar cambios")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.accept)

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(4)
        main_layout.addWidget(self._wrap_field("Contraseña actual", self.current_password_input))
        main_layout.addWidget(self._wrap_field("Nueva contraseña", self.new_password_input))
        main_layout.addWidget(self._wrap_field("Confirmar nueva contraseña", self.confirm_password_input))
        main_layout.addWidget(self.show_passwords_check)
        main_layout.addWidget(info_box)
        main_layout.addSpacing(4)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def _create_password_input(self, placeholder: str) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setEchoMode(QLineEdit.Password)
        line_edit.setMinimumHeight(40)
        return line_edit

    def _wrap_field(self, label_text: str, field: QLineEdit) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")

        layout.addWidget(label)
        layout.addWidget(field)
        wrapper.setLayout(layout)
        return wrapper

    def _toggle_password_visibility(self):
        echo_mode = (
            QLineEdit.Normal
            if self.show_passwords_check.isChecked()
            else QLineEdit.Password
        )

        self.current_password_input.setEchoMode(echo_mode)
        self.new_password_input.setEchoMode(echo_mode)
        self.confirm_password_input.setEchoMode(echo_mode)

    def get_password_data(self) -> dict:
        """Retorna los datos capturados por el formulario."""
        return {
            "current_password": self.current_password_input.text().strip(),
            "new_password": self.new_password_input.text().strip(),
            "confirm_password": self.confirm_password_input.text().strip(),
        }

    def clear_fields(self):
        """Limpia el formulario para reutilizar el diálogo si fuera necesario."""
        self.current_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        self.show_passwords_check.setChecked(False)
        self.current_password_input.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.current_password_input.setFocus(Qt.PopupFocusReason)

    def get_styles(self):
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
