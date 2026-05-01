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

from ca_program.services.course_service import CourseService
from ca_program.services.enrollment_service import EnrollmentService

try:
    from .course_card_widget import CourseCardWidget
except ImportError:
    # Compatibilidad temporal con la estructura anterior:
    # ca_program/views/*.py
    from ca_program.views.student_view.course_card_widget import CourseCardWidget


class AvailableCoursesWidget(QWidget):
    """Vista de cursos disponibles para usuarios con rol estudiante.

    Esta vista mantiene la responsabilidad visual de HU-18 y sirve como punto
    de entrada de HU-20 y HU-21. Muestra todos los cursos registrados, consulta
    el estado de inscripción del estudiante y delega las acciones a StudentGUI.
    """

    STATUS_NOT_ENROLLED = "NO_INSCRITO"
    STATUS_PENDING_PAYMENT = "PENDIENTE_DE_PAGO"
    STATUS_ENROLLED = "INSCRITO"
    STATUS_EXPIRED = "VENCIDO"

    def __init__(
        self,
        user=None,
        on_consult_course: Callable[[dict], None] | None = None,
        on_enroll_course: Callable[[dict], None] | None = None,
        on_pay_course: Callable[[dict], None] | None = None,
    ):
        super().__init__()
        self.user = user
        self.courses: list[dict] = []
        self.current_columns = 0
        self.empty_message_override: str | None = None
        self.on_consult_course = on_consult_course
        self.on_enroll_course = on_enroll_course
        self.on_pay_course = on_pay_course

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

        title = QLabel("Cursos disponibles")
        title.setObjectName("studentPageTitle")

        subtitle = QLabel("Explora la oferta académica disponible para iniciar tu formación.")
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

    def set_user(self, user):
        """Actualiza el usuario estudiante usado para consultar estados."""
        self.user = user
        self.load_courses()

    def set_consult_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que se ejecuta al consultar un curso."""
        self.on_consult_course = callback
        self._update_rendered_card_callbacks()

    def set_enroll_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que se ejecuta al solicitar inscripción."""
        self.on_enroll_course = callback
        self._schedule_populate_grid(self.empty_message_override)

    def set_payment_callback(self, callback: Callable[[dict], None] | None):
        """Define la acción que se ejecuta al pagar un recibo pendiente."""
        self.on_pay_course = callback
        self._schedule_populate_grid(self.empty_message_override)

    def set_course_action_callbacks(
        self,
        on_enroll_course: Callable[[dict], None] | None = None,
        on_pay_course: Callable[[dict], None] | None = None,
    ):
        """Configura en una sola llamada las acciones de HU-21."""
        self.on_enroll_course = on_enroll_course
        self.on_pay_course = on_pay_course
        self._schedule_populate_grid(self.empty_message_override)

    def load_courses(self):
        result = CourseService.get_courses()

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible consultar los cursos",
                result.get("message", "Ocurrió un error al consultar los cursos."),
            )
            self.courses = []
            self._schedule_populate_grid()
            return

        courses = result.get("courses", []) or result.get("data", []) or []
        self.courses = self._attach_enrollment_statuses(courses)
        self._schedule_populate_grid()

    def _attach_enrollment_statuses(self, courses: list[dict]) -> list[dict]:
        """Agrega estado de inscripción y recibo pendiente a cada curso.

        Si no hay usuario autenticado todavía, la vista conserva el
        comportamiento de HU-18: todos los cursos aparecen como disponibles y
        solo queda habilitada la consulta.
        """
        id_user = self._get_user_id()
        enriched_courses: list[dict] = []

        for course in courses:
            enriched_course = dict(course or {})
            enriched_course.setdefault("enrollment_status", self.STATUS_NOT_ENROLLED)
            enriched_course.setdefault("receipt", None)

            code_course = self._get_course_code(enriched_course)

            if id_user and code_course:
                status_result = EnrollmentService.get_course_enrollment_status(
                    id_user=id_user,
                    code_course=code_course,
                )

                if status_result.get("success"):
                    status = status_result.get("status") or self.STATUS_NOT_ENROLLED
                    enriched_course["enrollment_status"] = self._normalize_status(status)
                    enriched_course["receipt"] = status_result.get("receipt")
                    enriched_course["enrollment_status_message"] = status_result.get("message", "")
                else:
                    enriched_course["enrollment_status"] = "ESTADO_NO_DISPONIBLE"
                    enriched_course["enrollment_status_message"] = status_result.get(
                        "message",
                        "No fue posible consultar el estado de inscripción.",
                    )

            enriched_courses.append(enriched_course)

        return enriched_courses

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
            message = self.empty_message_override or "Aún no hay cursos registrados para mostrar."
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
                status_label=self._get_status_label(course),
            )
            self.grid_layout.addWidget(card, row, column, Qt.AlignTop | Qt.AlignLeft)

        self._add_grid_spacers(columns)

    def _get_action_config(self, course: dict) -> dict:
        status = self._normalize_status(course.get("enrollment_status"))

        if status == self.STATUS_NOT_ENROLLED and callable(self.on_enroll_course):
            return {
                "label": "Inscribirme",
                "callback": self._handle_enroll_course,
                "kind": "enroll",
                "enabled": True,
            }

        if status == self.STATUS_PENDING_PAYMENT and callable(self.on_pay_course):
            return {
                "label": "Pagar recibo",
                "callback": self._handle_pay_course,
                "kind": "payment",
                "enabled": True,
            }

        return {
            "label": None,
            "callback": None,
            "kind": "primary",
            "enabled": False,
        }

    def _get_status_label(self, course: dict) -> str:
        status = self._normalize_status(course.get("enrollment_status"))

        if status == self.STATUS_ENROLLED:
            return "Inscrito"
        if status == self.STATUS_PENDING_PAYMENT:
            return "Pendiente de pago"
        if status == "ESTADO_NO_DISPONIBLE":
            return "Disponible"
        return "Disponible"

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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

        if width >= 980:
            return 3
        if width >= 650:
            return 2
        return 1

    def _get_user_id(self):
        return getattr(self.user, "id_user", None)

    @staticmethod
    def _get_course_code(course: dict):
        return (
            course.get("code_course")
            or course.get("course_code")
            or course.get("code")
            or course.get("id")
        )

    def _handle_consult_course(self, course: dict):
        if callable(self.on_consult_course):
            self.on_consult_course(course)

    def _handle_enroll_course(self, course: dict):
        if callable(self.on_enroll_course):
            self.on_enroll_course(course)

    def _handle_pay_course(self, course: dict):
        if callable(self.on_pay_course):
            self.on_pay_course(course)

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

    def _normalize_status(self, status) -> str:
        status_text = str(status or self.STATUS_NOT_ENROLLED).strip().upper()

        aliases = {
            "NOT_ENROLLED": self.STATUS_NOT_ENROLLED,
            "NO INSCRITO": self.STATUS_NOT_ENROLLED,
            "DISPONIBLE": self.STATUS_NOT_ENROLLED,
            "PENDING_PAYMENT": self.STATUS_PENDING_PAYMENT,
            "PENDIENTE": self.STATUS_PENDING_PAYMENT,
            "PENDIENTE DE PAGO": self.STATUS_PENDING_PAYMENT,
            "ENROLLED": self.STATUS_ENROLLED,
            "CONFIRMADO": self.STATUS_ENROLLED,
            "VENCIDO": self.STATUS_EXPIRED,
            "EXPIRED": self.STATUS_EXPIRED,
            "ESTADO_NO_DISPONIBLE": "ESTADO_NO_DISPONIBLE",
        }

        return aliases.get(status_text, status_text)

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
