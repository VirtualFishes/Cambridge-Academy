from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


class CourseCardWidget(QFrame):
    """Tarjeta visual para presentar información básica de un curso.

    La tarjeta mantiene únicamente la acción de consulta. Las acciones de
    inscripción y pago quedan en la página de detalle del curso, donde el
    estudiante puede revisar toda la información antes de continuar.
    """

    def __init__(
        self,
        course: dict,
        on_consult: Callable[[dict], None] | None = None,
        status_label: str = "Disponible",
        on_action: Callable[[dict], None] | None = None,
        action_label: str | None = None,
        action_kind: str = "primary",
        action_enabled: bool = True,
    ):
        super().__init__()
        self.course = course
        self.on_consult = on_consult
        self.status_label = status_label

        # Compatibilidad con llamadas previas: se reciben estos parámetros,
        # pero no se dibuja una acción secundaria en la tarjeta.
        self.on_action = on_action
        self.action_label = action_label
        self.action_kind = action_kind
        self.action_enabled = action_enabled
        self.action_button: QPushButton | None = None
        self.button_layout: QHBoxLayout | None = None

        self.setObjectName("courseCard")
        self.setMinimumWidth(290)
        self.setMaximumWidth(340)
        self.setMinimumHeight(205)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel(self._get_course_name())
        title.setObjectName("courseTitle")
        title.setWordWrap(True)

        tag = QLabel(self.status_label)
        tag.setObjectName(self._get_tag_object_name())
        tag.setAlignment(Qt.AlignCenter)
        tag.setVisible(bool(self.status_label))

        header_layout.addWidget(title, 1)
        header_layout.addWidget(tag, 0, Qt.AlignTop)

        professor = QLabel(f"Profesor: {self._get_professor_name()}")
        professor.setObjectName("courseInfo")
        professor.setWordWrap(True)

        price = QLabel(f"Costo: {self._format_price(self.course.get('price'))}")
        price.setObjectName("coursePrice")

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)

        consult_button = QPushButton("Consultar")
        consult_button.setObjectName("consultButton")
        consult_button.setCursor(Qt.PointingHandCursor)
        consult_button.clicked.connect(self._handle_consult)

        # Botón único, alineado de forma estable al borde derecho inferior.
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(consult_button, 0, Qt.AlignRight)

        layout.addLayout(header_layout)
        layout.addWidget(professor)
        layout.addWidget(price)
        layout.addStretch()
        layout.addLayout(self.button_layout)

    def set_action(
        self,
        label: str | None,
        callback: Callable[[dict], None] | None,
        kind: str = "primary",
        enabled: bool = True,
    ):
        """Conserva compatibilidad con llamadas anteriores.

        La acción se guarda, pero no se dibuja en la tarjeta. El flujo de
        inscripción y pago se maneja desde la página de detalle del curso.
        """
        self.action_label = label
        self.on_action = callback
        self.action_kind = kind
        self.action_enabled = enabled

    def _handle_consult(self):
        if callable(self.on_consult):
            self.on_consult(self.course)

    def _handle_action(self):
        if callable(self.on_action):
            self.on_action(self.course)

    def _get_course_name(self) -> str:
        name = str(self.course.get("name", "")).strip()
        return name or "Curso sin nombre"

    def _get_professor_name(self) -> str:
        professor = self.course.get("professor") or {}
        professor_name = str(professor.get("name", "")).strip()
        return professor_name or "Sin profesor asignado"

    def _get_tag_object_name(self) -> str:
        normalized = str(self.status_label or "").strip().lower()

        if "pendiente" in normalized:
            return "courseTagPending"
        if "inscrito" in normalized:
            return "courseTagEnrolled"
        return "courseTag"

    def _get_action_object_name(self) -> str:
        normalized = str(self.action_kind or "").strip().lower()

        if normalized in {"payment", "pay", "pago", "receipt"}:
            return "paymentButton"
        return "enrollButton"

    def _format_price(self, price) -> str:
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            return "No registrado"

        if numeric_price <= 0:
            return "No registrado"

        formatted = f"{numeric_price:,.0f}".replace(",", ".")
        return f"$ {formatted}"
