"""Panel principal para usuarios estudiantes.

Coordina navegación entre vistas del estudiante y delega operaciones de inscripción, pago y seguridad a servicios."""

import importlib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.enrollment_service import EnrollmentService
from ca_program.services.account_service import AccountService
from ca_program.views.change_password_dialog import ChangePasswordDialog
from ca_program.views.student_view.student_view_utils import (
    get_course_code,
    get_course_name,
    get_user_id,
    normalize_enrollment_status,
)

try:
    from .available_courses_widget import AvailableCoursesWidget
    from .course_detail_widget import CourseDetailWidget
    from .enrolled_courses_widget import EnrolledCoursesWidget
    from .payment_dialog import PaymentDialog
    from .payments_record import PaymentsRecordWidget
    from .student_grade_record_widget import StudentGradeRecordWidget
except ImportError:
    # Compatibilidad temporal con la estructura anterior:
    # ca_program/views/*.py
    from ca_program.views.student_view.available_courses_widget import AvailableCoursesWidget
    from ca_program.views.student_view.course_detail_widget import CourseDetailWidget
    from ca_program.views.student_view.enrolled_courses_widget import EnrolledCoursesWidget
    from ca_program.views.student_view.payment_dialog import PaymentDialog
    from ca_program.views.student_view.payments_record import PaymentsRecordWidget
    from ca_program.views.student_view.student_grade_record_widget import StudentGradeRecordWidget


class StudentGUI(QMainWindow):
    """Panel principal para usuarios con rol estudiante."""

    AVAILABLE_COURSES_VIEW = "available_courses"
    ENROLLED_COURSES_VIEW = "enrolled_courses"
    PAYMENTS_RECORD_VIEW = "payments_record"
    GRADE_RECORD_VIEW = "grade_record"
    COURSE_DETAIL_VIEW = "course_detail"

    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.nav_buttons: dict[str, QPushButton] = {}
        self.views: dict[str, QWidget] = {}
        self.current_view_name = self.AVAILABLE_COURSES_VIEW
        self.previous_view_name = self.AVAILABLE_COURSES_VIEW

        self.setWindowTitle("Cambridge Academy | Estudiante")
        self.setMinimumSize(1180, 720)
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.change_view(self.AVAILABLE_COURSES_VIEW)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("studentRoot")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        self.stack = QStackedWidget()
        self.stack.setObjectName("studentContentStack")
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.available_courses_view = AvailableCoursesWidget(self.user)
        self.enrolled_courses_view = EnrolledCoursesWidget(self.user)
        self.payments_record_view = PaymentsRecordWidget(self.user)
        self.grade_record_view = StudentGradeRecordWidget(self.user)
        self.course_detail_view = CourseDetailWidget(on_back=self.return_to_previous_view)

        self._configure_course_consult_action(
            widget=self.available_courses_view,
            source_view_name=self.AVAILABLE_COURSES_VIEW,
        )
        self._configure_course_consult_action(
            widget=self.enrolled_courses_view,
            source_view_name=self.ENROLLED_COURSES_VIEW,
        )
        self._configure_course_action_callbacks(self.available_courses_view)
        self.course_detail_view.set_course_action_callbacks(
            on_enroll_course=self.handle_enroll_course,
            on_pay_course=self.handle_pay_course,
        )

        self.views = {
            self.AVAILABLE_COURSES_VIEW: self.available_courses_view,
            self.ENROLLED_COURSES_VIEW: self.enrolled_courses_view,
            self.PAYMENTS_RECORD_VIEW: self.payments_record_view,
            self.GRADE_RECORD_VIEW: self.grade_record_view,
            self.COURSE_DETAIL_VIEW: self.course_detail_view,
        }

        for view in self.views.values():
            self.stack.addWidget(view)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)

        self.statusBar().showMessage("Panel de estudiante listo")

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("studentSidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(10)

        brand = QLabel("CA")
        brand.setObjectName("studentBrandBadge")
        brand.setAlignment(Qt.AlignCenter)

        title = QLabel("Estudiante")
        title.setObjectName("studentSidebarTitle")
        title.setAlignment(Qt.AlignCenter)

        user_name = getattr(self.user, "name", "Estudiante")
        subtitle = QLabel(user_name)
        subtitle.setObjectName("studentSidebarSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(brand, alignment=Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self._add_nav_button(layout, self.AVAILABLE_COURSES_VIEW, "Cursos disponibles")
        self._add_nav_button(layout, self.ENROLLED_COURSES_VIEW, "Mis cursos")
        self._add_nav_button(layout, self.PAYMENTS_RECORD_VIEW, "Historial de pagos")
        self._add_nav_button(layout, self.GRADE_RECORD_VIEW, "Mis notas")

        layout.addStretch()

        self._add_action_button(layout, "Cambiar contraseña", self.open_change_password_dialog)

        logout_btn = QPushButton("Cerrar sesión")
        logout_btn.setObjectName("studentLogoutButton")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _add_nav_button(self, layout: QVBoxLayout, key: str, text: str):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setObjectName("studentNavButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda checked=False, view_key=key: self.change_view(view_key))
        self.nav_buttons[key] = button
        layout.addWidget(button)

    def _add_action_button(self, layout: QVBoxLayout, text: str, callback):
        button = QPushButton(text)
        button.setObjectName("studentSecurityButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        layout.addWidget(button)

    def _configure_course_consult_action(self, widget: QWidget, source_view_name: str):
        """Conecta la acción Consultar de una vista de cursos con HU-20.

        Esta integración mantiene compatibilidad con los widgets actuales, donde
        la acción estaba implementada como método interno, y con una futura
        versión más explícita mediante set_consult_callback().
        """

        def consult_course(course: dict, source=source_view_name):
            self.show_course_detail(course, source)

        if hasattr(widget, "set_consult_callback"):
            widget.set_consult_callback(consult_course)
            return

        if hasattr(widget, "on_consult_course"):
            widget.on_consult_course = consult_course
            return

        if hasattr(widget, "_handle_consult_course"):
            widget._handle_consult_course = consult_course
            self._replace_existing_card_callbacks(widget, consult_course)

    @staticmethod
    def _replace_existing_card_callbacks(widget: QWidget, consult_course):
        """Actualiza las tarjetas ya renderizadas sin volver a consultar la BD."""
        grid_layout = getattr(widget, "grid_layout", None)
        if grid_layout is None:
            return

        for index in range(grid_layout.count()):
            item = grid_layout.itemAt(index)
            if item is None:
                continue

            card = item.widget()
            if card is not None and hasattr(card, "on_consult"):
                card.on_consult = consult_course

    def change_view(self, view_name: str):
        view = self.views.get(view_name)
        if view is None:
            return

        self.stack.setCurrentWidget(view)

        if view_name == self.PAYMENTS_RECORD_VIEW and hasattr(self.payments_record_view, "load_payments"):
            self.payments_record_view.load_payments()

        if view_name == self.GRADE_RECORD_VIEW and hasattr(self.grade_record_view, "load_records"):
            self.grade_record_view.load_records()

        if view_name != self.COURSE_DETAIL_VIEW:
            self.current_view_name = view_name

        for key, button in self.nav_buttons.items():
            button.setChecked(key == view_name)

        labels = {
            self.AVAILABLE_COURSES_VIEW: "Cursos disponibles",
            self.ENROLLED_COURSES_VIEW: "Mis cursos",
            self.PAYMENTS_RECORD_VIEW: "Historial de pagos",
            self.GRADE_RECORD_VIEW: "Mis notas",
            self.COURSE_DETAIL_VIEW: "Detalle del curso",
        }
        self.statusBar().showMessage(labels.get(view_name, "Panel de estudiante"))

    def show_course_detail(self, course: dict, previous_view_name: str | None = None):
        """Abre la página de detalle para el curso seleccionado."""
        if not isinstance(course, dict):
            return

        source_view = previous_view_name or self.current_view_name or self.AVAILABLE_COURSES_VIEW
        if source_view == self.COURSE_DETAIL_VIEW or source_view not in self.views:
            source_view = self.AVAILABLE_COURSES_VIEW

        self.previous_view_name = source_view
        self.course_detail_view.set_course(self._enrich_course_with_status(course))
        self.change_view(self.COURSE_DETAIL_VIEW)

        for button in self.nav_buttons.values():
            button.setChecked(False)

    def return_to_previous_view(self):
        """Regresa desde el detalle del curso a la vista de origen."""
        target_view = self.previous_view_name
        if target_view not in self.views or target_view == self.COURSE_DETAIL_VIEW:
            target_view = self.AVAILABLE_COURSES_VIEW

        self.change_view(target_view)

    def _configure_course_action_callbacks(self, widget: QWidget):
        """Conecta las acciones de inscripción y pago de HU-21."""
        if hasattr(widget, "set_course_action_callbacks"):
            widget.set_course_action_callbacks(
                on_enroll_course=self.handle_enroll_course,
                on_pay_course=self.handle_pay_course,
            )
            return

        if hasattr(widget, "set_enroll_callback"):
            widget.set_enroll_callback(self.handle_enroll_course)

        if hasattr(widget, "set_payment_callback"):
            widget.set_payment_callback(self.handle_pay_course)

    def handle_enroll_course(self, course: dict):
        """Solicita la inscripción y, si procede, permite pagar el recibo generado."""
        id_user = self._get_user_id()
        code_course = self._get_course_code(course)

        if not id_user:
            QMessageBox.warning(
                self,
                "Usuario no identificado",
                "No fue posible identificar el usuario estudiante autenticado.",
            )
            return

        if not code_course:
            QMessageBox.warning(
                self,
                "Curso no identificado",
                "No fue posible identificar el curso seleccionado.",
            )
            return

        course_name = self._get_course_name(course)
        confirmation = QMessageBox.question(
            self,
            "Confirmar inscripción",
            (
                f"¿Deseas iniciar la inscripción al curso {course_name}?\n\n"
                "El sistema generará un recibo pendiente con 10 días de plazo para pagarlo."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation != QMessageBox.Yes:
            return

        result = EnrollmentService.request_course_enrollment(
            id_user=id_user,
            code_course=code_course,
        )

        updated_course = self._merge_course_service_result(course, result)
        self._refresh_student_views()

        if not result.get("success"):
            QMessageBox.warning(
                self,
                "No fue posible iniciar la inscripción",
                result.get("message", "Ocurrió un error durante la inscripción."),
            )
            self._refresh_detail_if_visible(updated_course)
            return

        receipt = updated_course.get("receipt")
        status = self._normalize_status(updated_course.get("enrollment_status"))

        if status == "PENDIENTE_DE_PAGO" and receipt:
            pay_now = QMessageBox.question(
                self,
                "Recibo pendiente generado",
                (
                    f"{result.get('message', 'Se generó un recibo pendiente.')}\n\n"
                    "¿Deseas pagar el recibo ahora?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if pay_now == QMessageBox.Yes:
                self._open_payment_dialog(updated_course, receipt)
            else:
                self._refresh_detail_if_visible(updated_course)
            return

        QMessageBox.information(
            self,
            "Inscripción",
            result.get("message", "La solicitud de inscripción fue procesada."),
        )
        self._refresh_detail_if_visible(updated_course)

    def handle_pay_course(self, course: dict):
        """Abre el pago simulado para el recibo pendiente de un curso."""
        id_user = self._get_user_id()
        code_course = self._get_course_code(course)

        if not id_user:
            QMessageBox.warning(
                self,
                "Usuario no identificado",
                "No fue posible identificar el usuario estudiante autenticado.",
            )
            return

        if not code_course:
            QMessageBox.warning(
                self,
                "Curso no identificado",
                "No fue posible identificar el curso seleccionado.",
            )
            return

        updated_course = self._enrich_course_with_status(course)
        status = self._normalize_status(updated_course.get("enrollment_status"))
        receipt = updated_course.get("receipt")

        if status == "INSCRITO":
            QMessageBox.information(
                self,
                "Inscripción confirmada",
                "Este curso ya tiene una inscripción confirmada.",
            )
            self._refresh_detail_if_visible(updated_course)
            return

        if status != "PENDIENTE_DE_PAGO" or not receipt:
            QMessageBox.warning(
                self,
                "Recibo no disponible",
                "No existe un recibo pendiente vigente para este curso.",
            )
            self._refresh_student_views()
            self._refresh_detail_if_visible(updated_course)
            return

        self._open_payment_dialog(updated_course, receipt)

    def _open_payment_dialog(self, course: dict, receipt: dict | object):
        """Muestra el diálogo de pago y delega el registro al servicio."""
        dialog = PaymentDialog(course=course, receipt=receipt, parent=self)

        if dialog.exec() != QDialog.Accepted:
            self._refresh_detail_if_visible(course)
            return

        result = EnrollmentService.pay_enrollment_receipt(
            id_user=self._get_user_id(),
            code_course=self._get_course_code(course),
            payment_method=dialog.selected_payment_method(),
        )

        updated_course = self._merge_course_service_result(course, result)
        self._refresh_student_views()

        if result.get("success"):
            QMessageBox.information(
                self,
                "Pago exitoso",
                result.get(
                    "message",
                    "Pago registrado correctamente. Tu inscripción ha sido completada.",
                ),
            )
        else:
            QMessageBox.warning(
                self,
                "No fue posible registrar el pago",
                result.get("message", "Ocurrió un error al registrar el pago."),
            )

        refreshed_course = self._enrich_course_with_status(updated_course)
        self._refresh_detail_if_visible(refreshed_course)

    def _refresh_student_views(self):
        """Actualiza las vistas que dependen del estado de inscripción."""
        if hasattr(self.available_courses_view, "load_courses"):
            self.available_courses_view.load_courses()

        if hasattr(self.enrolled_courses_view, "load_courses"):
            self.enrolled_courses_view.load_courses()

        if hasattr(self.payments_record_view, "load_payments"):
            self.payments_record_view.load_payments()

        if hasattr(self.grade_record_view, "load_records"):
            self.grade_record_view.load_records(show_error=False)

    def _refresh_detail_if_visible(self, course: dict):
        if getattr(self, "stack", None) and self.stack.currentWidget() == self.course_detail_view:
            self.course_detail_view.set_course(course)

    def _enrich_course_with_status(self, course: dict) -> dict:
        """Agrega al curso el estado actual de inscripción del estudiante."""
        enriched_course = dict(course or {})
        id_user = self._get_user_id()
        code_course = self._get_course_code(enriched_course)

        if not id_user or not code_course:
            enriched_course.setdefault("enrollment_status", "NO_INSCRITO")
            enriched_course.setdefault("receipt", None)
            return enriched_course

        status_result = EnrollmentService.get_course_enrollment_status(
            id_user=id_user,
            code_course=code_course,
        )

        if status_result.get("success"):
            return self._merge_course_service_result(enriched_course, status_result)

        enriched_course.setdefault("enrollment_status", "NO_INSCRITO")
        enriched_course["enrollment_status_message"] = status_result.get(
            "message",
            "No fue posible consultar el estado de inscripción.",
        )
        return enriched_course

    @staticmethod
    def _merge_course_service_result(course: dict, result: dict) -> dict:
        """Combina los datos visibles del curso con la respuesta de EnrollmentService."""
        updated_course = dict(course or {})
        data = result.get("data") or {}
        service_course = result.get("course") or data.get("course") or {}

        if isinstance(service_course, dict) and service_course:
            updated_course.update(service_course)

        status = result.get("status") or data.get("status")
        if status:
            updated_course["enrollment_status"] = status

        receipt = result.get("receipt") or data.get("receipt")
        if receipt is not None:
            updated_course["receipt"] = receipt
        elif status == "NO_INSCRITO":
            updated_course["receipt"] = None

        message = result.get("message")
        if message:
            updated_course["enrollment_status_message"] = message

        return updated_course

    def _get_user_id(self):
        """Obtiene el id_user sin acoplar la GUI a una implementación concreta."""
        return get_user_id(self.user)

    @staticmethod
    def _get_course_code(course: dict):
        """Obtiene el código de curso desde las claves aceptadas por la GUI."""
        return get_course_code(course)

    @staticmethod
    def _get_course_name(course: dict) -> str:
        """Obtiene el nombre visible del curso para mensajes de confirmación."""
        return get_course_name(course)

    @staticmethod
    def _normalize_status(status) -> str:
        """Normaliza estados de inscripción devueltos por servicios."""
        return normalize_enrollment_status(status)

    def open_change_password_dialog(self):
        """Abre el diálogo de cambio de contraseña para el estudiante autenticado."""
        id_user = self._get_user_id()

        if not id_user:
            QMessageBox.warning(
                self,
                "Usuario no identificado",
                "No fue posible identificar el usuario autenticado.",
            )
            return

        dialog = ChangePasswordDialog(parent=self)

        if dialog.exec() != QDialog.Accepted:
            return

        password_data = dialog.get_password_data()
        result = AccountService.change_password(
            id_user=id_user,
            current_password=password_data.get("current_password"),
            new_password=password_data.get("new_password"),
            confirm_password=password_data.get("confirm_password"),
        )

        if result.get("success"):
            QMessageBox.information(
                self,
                "Contraseña actualizada",
                result.get("message", "Contraseña actualizada correctamente."),
            )
        else:
            QMessageBox.warning(
                self,
                "No fue posible cambiar la contraseña",
                result.get("message", "Ocurrió un error al cambiar la contraseña."),
            )

    def logout(self):
        LoginWindow = self._get_login_window_class()
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    @staticmethod
    def _get_login_window_class():
        """Obtiene la ventana de inicio de sesión según la estructura vigente."""
        try:
            login_module = importlib.import_module("ca_program.views.login_view")
        except ModuleNotFoundError:
            login_module = importlib.import_module("ca_program.views.login_gui")

        login_window = getattr(login_module, "LoginGUI", None)
        if login_window is not None:
            return login_window

        login_window = getattr(login_module, "LoginView", None)
        if login_window is not None:
            return login_window

        raise ImportError("No se encontró LoginGUI ni LoginView en el módulo de login.")

    def get_styles(self) -> str:
        return """
        QMainWindow, QWidget#studentRoot {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#studentSidebar {
            background-color: #1e3a8a;
            border: none;
        }

        QLabel#studentBrandBadge {
            background-color: #16a34a;
            color: white;
            border-radius: 28px;
            min-width: 56px;
            min-height: 56px;
            max-width: 56px;
            max-height: 56px;
            font-size: 22px;
            font-weight: 800;
        }

        QLabel#studentSidebarTitle {
            color: white;
            font-size: 20px;
            font-weight: 700;
            padding-top: 8px;
        }

        QLabel#studentSidebarSubtitle {
            color: #c7d2fe;
            font-size: 13px;
            padding-bottom: 8px;
        }

        QPushButton#studentNavButton {
            background-color: transparent;
            color: #dbeafe;
            text-align: left;
            border: none;
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 600;
        }

        QPushButton#studentNavButton:hover {
            background-color: rgba(255, 255, 255, 0.12);
            color: white;
        }

        QPushButton#studentNavButton:checked {
            background-color: #2563eb;
            color: white;
        }

        QPushButton#studentSecurityButton {
            background-color: rgba(255, 255, 255, 0.10);
            color: #dbeafe;
            text-align: left;
            border: 1px solid rgba(191, 219, 254, 0.35);
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QPushButton#studentSecurityButton:hover {
            background-color: rgba(255, 255, 255, 0.18);
            color: white;
            border-color: rgba(255, 255, 255, 0.55);
        }

        QPushButton#studentLogoutButton {
            background-color: #16a34a;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QPushButton#studentLogoutButton:hover {
            background-color: #15803d;
        }

        QWidget#studentContentStack, QWidget#coursesScrollContent {
            background-color: #eaf0f8;
        }

        QLabel#studentPageTitle {
            color: #1e3a8a;
            font-size: 28px;
            font-weight: 800;
        }

        QLabel#studentPageSubtitle {
            color: #475569;
            font-size: 14px;
        }

        QPushButton#secondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 700;
        }

        QPushButton#secondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }

        QScrollArea#coursesScrollArea {
            background-color: transparent;
            border: none;
        }

        QFrame#coursesPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QFrame#courseCard {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QFrame#courseCard:hover {
            border: 1px solid #93c5fd;
            background-color: #f8fbff;
        }

        QLabel#courseTitle {
            color: #0f172a;
            font-size: 18px;
            font-weight: 800;
        }

        QLabel#courseTag {
            background-color: #dcfce7;
            color: #166534;
            padding: 5px 9px;
            border-radius: 9px;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#courseInfo {
            color: #475569;
            font-size: 14px;
            font-weight: 500;
        }

        QLabel#coursePrice {
            color: #1e3a8a;
            font-size: 16px;
            font-weight: 800;
        }

        QPushButton#consultButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 9px 16px;
            font-weight: 700;
        }

        QPushButton#consultButton:hover {
            background-color: #1d4ed8;
        }

        QFrame#paymentsSummaryPanel, QFrame#paymentsPanel {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
        }

        QFrame#paymentSummaryCard {
            background-color: #f8fbff;
            border: 1px solid #dbe4f0;
            border-radius: 14px;
        }

        QLabel#paymentSummaryLabel {
            color: #64748b;
            font-size: 13px;
            font-weight: 700;
        }

        QLabel#paymentSummaryValue {
            color: #1e3a8a;
            font-size: 20px;
            font-weight: 900;
        }

        QScrollArea#paymentsScrollArea {
            background-color: transparent;
            border: none;
        }

        QWidget#paymentsScrollContent {
            background-color: white;
        }

        QFrame#paymentRecordCard {
            background-color: #ffffff;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QFrame#paymentRecordCard:hover {
            border-color: #93c5fd;
            background-color: #f8fbff;
        }

        QLabel#paymentCourseTitle {
            color: #0f172a;
            font-size: 18px;
            font-weight: 900;
        }

        QLabel#paymentReceiptLabel, QLabel#paymentFooterLabel {
            color: #64748b;
            font-size: 13px;
            font-weight: 600;
        }

        QLabel#paymentAmountBadge {
            background-color: #dcfce7;
            color: #166534;
            border-radius: 12px;
            padding: 8px 12px;
            font-size: 16px;
            font-weight: 900;
        }

        QFrame#paymentDetailItem {
            background-color: #f8fbff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }

        QLabel#paymentDetailLabel {
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
        }

        QLabel#paymentDetailValue {
            color: #1e293b;
            font-size: 14px;
            font-weight: 700;
        }

        QFrame#paymentEmptyState {
            background-color: #f8fbff;
            border: 1px dashed #cbd5e1;
            border-radius: 16px;
            min-height: 280px;
        }

        QLabel#paymentEmptyTitle {
            color: #1e3a8a;
            font-size: 20px;
            font-weight: 900;
        }

        QLabel#paymentEmptyDetail {
            color: #64748b;
            font-size: 14px;
            font-weight: 600;
        }


        QScrollBar:vertical, QScrollBar:horizontal {
            background-color: #f1f5f9;
            border: none;
            margin: 0px;
        }

        QScrollBar:vertical {
            width: 10px;
        }

        QScrollBar:horizontal {
            height: 10px;
        }

        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background-color: #94a3b8;
            border-radius: 5px;
            min-height: 28px;
            min-width: 28px;
        }

        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background-color: #64748b;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            width: 0px;
            height: 0px;
        }
        QLabel#emptyState {
            background-color: white;
            color: #64748b;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
            padding: 36px;
            font-size: 16px;
            font-weight: 600;
        }
        """
