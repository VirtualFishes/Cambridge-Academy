"""
Utilidades reutilizables para los componentes de la capa Views.

Este módulo agrupa funciones pequeñas de apoyo visual para evitar duplicación
entre pantallas. No contiene reglas de negocio, consultas a base de datos ni
llamadas directas a modelos; su propósito es mantener las vistas simples y
consistentes.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget


PASSWORD_ECHO_MODE = QLineEdit.Password
VISIBLE_TEXT_ECHO_MODE = QLineEdit.Normal


def create_password_input(placeholder: str, minimum_height: int = 40) -> QLineEdit:
    """
    Crea un campo de contraseña con configuración visual estándar.

    Las vistas que pidan contraseñas deben comportarse igual: texto oculto por
    defecto, altura suficiente y placeholder claro para el usuario final.
    """
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(str(placeholder or ""))
    line_edit.setEchoMode(PASSWORD_ECHO_MODE)
    line_edit.setMinimumHeight(minimum_height)
    return line_edit


def wrap_labeled_field(label_text: str, field: QWidget) -> QWidget:
    """
    Envuelve un campo de formulario con una etiqueta superior.

    Esta función mantiene una estructura visual uniforme sin repetir el mismo
    bloque de layout en cada vista.
    """
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    label = QLabel(str(label_text or ""))
    label.setObjectName("fieldLabel")

    layout.addWidget(label)
    layout.addWidget(field)
    return wrapper


def set_password_fields_visible(fields: list[QLineEdit], visible: bool) -> None:
    """
    Cambia la visibilidad de un conjunto de campos de contraseña.

    Recibe una lista para evitar repetir la misma llamada sobre cada campo en
    los formularios que manejan varias contraseñas.
    """
    echo_mode = VISIBLE_TEXT_ECHO_MODE if visible else PASSWORD_ECHO_MODE
    for field in fields:
        if isinstance(field, QLineEdit):
            field.setEchoMode(echo_mode)


def clean_text(value: Any) -> str:
    """
    Normaliza texto capturado desde la interfaz.

    La limpieza aquí es puramente de presentación/captura; las validaciones de
    negocio siguen perteneciendo a la capa Services.
    """
    return str(value or "").strip()


def get_user_role_name(user: Any) -> str:
    """
    Obtiene el nombre del rol de un usuario de forma tolerante.

    Soporta entidades con Enum, objetos con atributo role o diccionarios usados
    en pruebas. Retorna una cadena en mayúsculas para simplificar el enrutado
    visual posterior al inicio de sesión.
    """
    if user is None:
        return ""

    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    if role is None:
        return ""

    role_name = getattr(role, "name", None)
    if role_name:
        return str(role_name).upper()

    role_value = getattr(role, "value", role)
    normalized_value = str(role_value).strip().lower()

    aliases = {
        "administrator": "ADMIN",
        "admin": "ADMIN",
        "student": "STUDENT",
        "professor": "PROFESSOR",
    }
    return aliases.get(normalized_value, normalized_value.upper())


def show_warning(parent: QWidget, title: str, message: str) -> None:
    """Muestra un mensaje de advertencia con estilo estándar de Qt."""
    QMessageBox.warning(parent, title, message)


def show_information(parent: QWidget, title: str, message: str) -> None:
    """Muestra un mensaje informativo con estilo estándar de Qt."""
    QMessageBox.information(parent, title, message)


def show_critical(parent: QWidget, title: str, message: str) -> None:
    """Muestra un mensaje crítico cuando la vista no puede continuar."""
    QMessageBox.critical(parent, title, message)
