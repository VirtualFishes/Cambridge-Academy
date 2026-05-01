"""Vista de cursos inscritos del estudiante.

Consulta las inscripciones confirmadas mediante EnrollmentService y presenta tarjetas de solo lectura."""

from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.enrollment_service import EnrollmentService
from ca_program.views.student_view.student_view_utils import (
    calculate_card_columns,
    clear_layout,
    get_user_id,
)

try:
    from .course_card_widget import CourseCardWidget
except ImportError:
    # Compatibilidad temporal con la estructura anterior:
    # ca_program/views/*.py
    from ca_program.views.student_view.course_card_widget import CourseCardWidget


class EnrolledCoursesWidget(QWidget):
    """Vista de cursos inscritos para usuarios con rol estudiante.

    Esta vista pertenece a HU-19 y se conecta con HU-20 mediante un callback
    externo para consultar el detalle del curso seleccionado. La vista conserva
    una responsabilidad simple: consultar los cursos inscritos del estudiante y
    presentar tarjetas de solo lectura.
    """

    def __init__(
        self,
        user=None,
        on_consult_course: Callable[[dict], None] | None = None,
    ):
        super().__init__()
        self.user = user
        self.courses: list[dict] = []
        self.current_columns = 0
        self.empty_message_override: str | None = None
        self.on_consult_course = on_consult_course

        self._build_ui()
        self.load_courses()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("studentHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("Mis cursos")
        title.setObjectName("studentPageTitle")

        subtitle = QLabel("Consulta los cursos en los que actualmente estás inscrito.")
        subtitle.setObjectName("studentPageSubtitle")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.load_courses)

        header_layout.addWidget(title_container, 1)
        header_layout.addWidget(refresh_button, 0, Qt.AlignTop)

        self.courses_panel = QFrame()
        self.courses_panel.setObjectName("coursesPanel")
        panel_layout = QVBoxLayout(self.courses_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("coursesScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("coursesScrollContent")
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

    def set_consult_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que se ejecuta al consultar un curso inscrito.

        StudentGUI usa este método para conectar el botón Consultar con la
        página de detalle de HU-20. Esta vista no decide la navegación.
        """
        self.on_consult_course = callback
        self._update_rendered_card_callbacks()

    def load_courses(self):
        id_user = self._get_user_id()

        if not id_user:
            self.courses = []
            self._schedule_populate_grid(
                "No fue posible identificar el usuario estudiante autenticado."
            )
            return

        result = EnrollmentService.get_enrolled_courses_by_student_user_id(id_user)

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible consultar los cursos inscritos",
                result.get("message", "Ocurrió un error al consultar los cursos inscritos."),
            )
            self.courses = []
            self._schedule_populate_grid()
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
            message = self.empty_message_override or "Aún no tienes cursos inscritos para mostrar."
            empty_message = QLabel(message)
            empty_message.setObjectName("emptyState")
            empty_message.setAlignment(Qt.AlignCenter)
            empty_message.setWordWrap(True)
            self.grid_layout.addWidget(empty_message, 0, 0, 1, columns, Qt.AlignCenter)
            return

        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        for index, course in enumerate(self.courses):
            row = index // columns
            column = index % columns
            card = CourseCardWidget(
                course,
                on_consult=self._handle_consult_course,
                status_label="Inscrito",
            )
            self.grid_layout.addWidget(card, row, column, Qt.AlignTop | Qt.AlignLeft)

        self._add_grid_spacers(columns)

    def _clear_grid(self):
        """Limpia las tarjetas actuales antes de renderizar nuevamente."""
        clear_layout(self.grid_layout)

    def _reset_grid_stretches(self):
        rows_to_reset = max(12, (len(self.courses) // 3) + 4)
        for row in range(rows_to_reset):
            self.grid_layout.setRowStretch(row, 0)

        for column in range(4):
            self.grid_layout.setColumnStretch(column, 0)

    def _add_grid_spacers(self, columns: int):
        for column in range(columns):
            self.grid_layout.setColumnStretch(column, 0)

        # Esta columna absorbe el espacio libre y mantiene las tarjetas
        # alineadas a la izquierda, no centradas en el panel.
        self.grid_layout.setColumnStretch(columns, 1)

        last_row = ((len(self.courses) - 1) // columns) + 1
        self.grid_layout.setRowStretch(last_row, 1)

    def _calculate_columns(self) -> int:
        width = max(
            self.courses_panel.width() if hasattr(self, "courses_panel") else 0,
            self.scroll_area.viewport().width() if hasattr(self, "scroll_area") else 0,
            self.width(),
        )

        return calculate_card_columns(width)

    def _get_user_id(self):
        """Obtiene el usuario autenticado sin acoplarse a una clase concreta."""
        return get_user_id(self.user)

    def _handle_consult_course(self, course: dict):
        if callable(self.on_consult_course):
            self.on_consult_course(course)

    def _update_rendered_card_callbacks(self):
        if not hasattr(self, "grid_layout"):
            return

        for index in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(index)
            if item is None:
                continue

            card = item.widget()
            if card is not None and hasattr(card, "on_consult"):
                card.on_consult = self._handle_consult_course

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
