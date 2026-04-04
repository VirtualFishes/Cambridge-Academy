"""
Vista del panel de administración.
Solo accesible para usuarios con rol 'admin'.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy, QStackedWidget, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

from ca_program.services.auth_service import AuthService
from ca_program.models.user_model import UserModel
from ca_program.entities.user import User


# ──────────────────────────────────────────────────────────────────────────────
# Estilos
# ──────────────────────────────────────────────────────────────────────────────

COLORS = {
    "bg":           "#0d0d0d",
    "sidebar":      "#111111",
    "card":         "#161616",
    "border":       "#222222",
    "accent":       "#4f8ef7",
    "accent_hover": "#3a72d8",
    "danger":       "#e05c5c",
    "danger_hover": "#c04040",
    "text":         "#f0f0f0",
    "subtext":      "#777777",
    "row_alt":      "#1a1a1a",
    "selected":     "#1c2e4a",
}

STYLESHEET = f"""
QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}}

/* ── Sidebar ── */
QFrame#sidebar {{
    background-color: {COLORS['sidebar']};
    border-right: 1px solid {COLORS['border']};
}}

QLabel#app_name {{
    color: {COLORS['accent']};
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 0px 20px;
}}

QLabel#app_version {{
    color: {COLORS['subtext']};
    font-size: 10px;
    padding: 0px 20px;
}}

QPushButton#nav_btn {{
    background: transparent;
    color: {COLORS['subtext']};
    border: none;
    text-align: left;
    padding: 10px 20px;
    font-size: 13px;
    border-radius: 0px;
}}

QPushButton#nav_btn:hover {{
    background-color: {COLORS['border']};
    color: {COLORS['text']};
}}

QPushButton#nav_btn:checked {{
    background-color: #1c2e4a;
    color: {COLORS['accent']};
    border-left: 3px solid {COLORS['accent']};
}}

/* ── Topbar ── */
QFrame#topbar {{
    background-color: {COLORS['card']};
    border-bottom: 1px solid {COLORS['border']};
}}

QLabel#page_title {{
    font-size: 18px;
    font-weight: 600;
    color: {COLORS['text']};
}}

QLabel#user_info {{
    color: {COLORS['subtext']};
    font-size: 12px;
}}

/* ── Cards ── */
QFrame#stat_card {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 8px;
}}

QLabel#stat_value {{
    font-size: 28px;
    font-weight: 700;
    color: {COLORS['accent']};
}}

QLabel#stat_label {{
    font-size: 11px;
    color: {COLORS['subtext']};
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ── Tabla ── */
QTableWidget {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['selected']};
}}

QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['selected']};
    color: {COLORS['text']};
}}

QHeaderView::section {{
    background-color: {COLORS['sidebar']};
    color: {COLORS['subtext']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    text-transform: uppercase;
}}

/* ── Botones ── */
QPushButton#btn_primary {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 7px;
    padding: 9px 18px;
    font-weight: 600;
}}

QPushButton#btn_primary:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#btn_danger {{
    background-color: transparent;
    color: {COLORS['danger']};
    border: 1px solid {COLORS['danger']};
    border-radius: 7px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 12px;
}}

QPushButton#btn_danger:hover {{
    background-color: {COLORS['danger']};
    color: white;
}}

QPushButton#btn_logout {{
    background: transparent;
    color: {COLORS['danger']};
    border: none;
    font-size: 12px;
    text-align: left;
    padding: 10px 20px;
}}

QPushButton#btn_logout:hover {{
    color: white;
    background-color: {COLORS['danger']};
}}

/* ── Scroll ── */
QScrollBar:vertical {{
    background: {COLORS['bg']};
    width: 6px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 3px;
}}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Panel de administración
# ──────────────────────────────────────────────────────────────────────────────

class AdminGUI(QWidget):
    """Panel de control para usuarios administrativos."""

    def __init__(self, auth_service: AuthService = None):
        super().__init__()

        self._auth = auth_service or AuthService()
        self._user_model = UserModel()
        self._current_user = self._auth.get_current_user()

        self.setWindowTitle("Panel de Administración")
        self.resize(1000, 660)
        self.setStyleSheet(STYLESHEET)
        self._center_window()
        self._build_ui()
        self._load_users()

    def _center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        # Área principal
        main_area = QVBoxLayout()
        main_area.setContentsMargins(0, 0, 0, 0)
        main_area.setSpacing(0)
        main_area.addWidget(self._build_topbar())
        main_area.addLayout(self._build_content())

        main_widget = QWidget()
        main_widget.setLayout(main_area)
        root.addWidget(main_widget)

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo / nombre
        layout.addSpacing(24)
        app_name = QLabel("CA PROGRAM")
        app_name.setObjectName("app_name")
        layout.addWidget(app_name)

        version = QLabel("Sistema académico v1.0")
        version.setObjectName("app_version")
        layout.addWidget(version)
        layout.addSpacing(28)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)
        layout.addSpacing(12)

        # Navegación
        nav_label = QLabel("MENÚ")
        nav_label.setStyleSheet(
            f"color:{COLORS['subtext']}; font-size:10px;"
            f"font-weight:600; letter-spacing:1px; padding:0 20px;"
        )
        layout.addWidget(nav_label)
        layout.addSpacing(6)

        self.btn_users = QPushButton("👥  Usuarios")
        self.btn_users.setObjectName("nav_btn")
        self.btn_users.setCheckable(True)
        self.btn_users.setChecked(True)
        self.btn_users.clicked.connect(lambda: self._switch_page(0))
        layout.addWidget(self.btn_users)

        layout.addStretch()

        # Logout
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep2)

        btn_logout = QPushButton("⇤  Cerrar sesión")
        btn_logout.setObjectName("btn_logout")
        btn_logout.clicked.connect(self._logout)
        layout.addWidget(btn_logout)
        layout.addSpacing(10)

        return sidebar

    # ── Topbar ───────────────────────────────────────────────────────────────

    def _build_topbar(self) -> QFrame:
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(60)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(28, 0, 28, 0)

        self.lbl_page_title = QLabel("Gestión de Usuarios")
        self.lbl_page_title.setObjectName("page_title")
        layout.addWidget(self.lbl_page_title)

        layout.addStretch()

        username = self._current_user.name if self._current_user else "Administrador"
        user_info = QLabel(f"🔒  {username}  ·  Administrador")
        user_info.setObjectName("user_info")
        layout.addWidget(user_info)

        return topbar

    # ── Contenido ────────────────────────────────────────────────────────────

    def _build_content(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Stats cards
        layout.addLayout(self._build_stats_row())

        # Encabezado tabla
        header_row = QHBoxLayout()
        tbl_title = QLabel("Todos los usuarios")
        tbl_title.setStyleSheet("font-size:15px; font-weight:600;")
        header_row.addWidget(tbl_title)
        header_row.addStretch()

        btn_refresh = QPushButton("↺  Actualizar")
        btn_refresh.setObjectName("btn_primary")
        btn_refresh.clicked.connect(self._load_users)
        header_row.addWidget(btn_refresh)
        layout.addLayout(header_row)

        # Tabla de usuarios
        self.table = self._build_table()
        layout.addWidget(self.table)

        return layout

    def _build_stats_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)

        self.card_total = self._stat_card("—", "Total usuarios")
        self.card_admins = self._stat_card("—", "Administradores")
        self.card_profs = self._stat_card("—", "Profesores")
        self.card_students = self._stat_card("—", "Estudiantes")

        for card in [self.card_total, self.card_admins, self.card_profs, self.card_students]:
            row.addWidget(card)
        return row

    def _stat_card(self, value: str, label: str) -> QFrame:
        card = QFrame()
        card.setObjectName("stat_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        lbl_val = QLabel(value)
        lbl_val.setObjectName("stat_value")

        lbl_name = QLabel(label)
        lbl_name.setObjectName("stat_label")

        layout.addWidget(lbl_val)
        layout.addWidget(lbl_name)

        # Guardamos referencia al valor
        card._value_label = lbl_val
        return card

    def _build_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "NOMBRE", "ROL", "ESTADO", "ACCIÓN"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(False)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.NoFocus)
        return table

    # ── Datos ────────────────────────────────────────────────────────────────

    def _load_users(self):
        users = self._user_model.get_all_users()
        self.table.setRowCount(0)

        counts = {"admin": 0, "professor": 0, "student": 0}

        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            role_display = {
                "admin": "Administrador",
                "professor": "Profesor",
                "student": "Estudiante",
            }.get(user.role, user.role)

            role_color = {
                "admin": "#4f8ef7",
                "professor": "#7ecb7e",
                "student": "#f0b84f",
            }.get(user.role, COLORS["subtext"])

            # Celdas
            id_item = QTableWidgetItem(str(user.id_user))
            id_item.setTextAlignment(Qt.AlignCenter)

            name_item = QTableWidgetItem(user.name)
            role_item = QTableWidgetItem(role_display)
            role_item.setForeground(QColor(role_color))

            status_item = QTableWidgetItem("Activo")
            status_item.setForeground(QColor("#7ecb7e"))
            status_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, role_item)
            self.table.setItem(row, 3, status_item)

            # Botón eliminar
            btn = QPushButton("Eliminar")
            btn.setObjectName("btn_danger")
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked, u=user: self._confirm_delete(u))

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(8, 4, 8, 4)
            btn_layout.addWidget(btn)
            self.table.setCellWidget(row, 4, btn_container)
            self.table.setRowHeight(row, 46)

            if user.role in counts:
                counts[user.role] += 1

        # Actualizar tarjetas de estadísticas
        self.card_total._value_label.setText(str(len(users)))
        self.card_admins._value_label.setText(str(counts["admin"]))
        self.card_profs._value_label.setText(str(counts["professor"]))
        self.card_students._value_label.setText(str(counts["student"]))

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _confirm_delete(self, user: User):
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar al usuario '{user.name}'?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            from ca_program.models.user_model import UserModel
            model = UserModel()
            success = model.delete_user(user.id_user)
            if success:
                self._load_users()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el usuario.")

    def _switch_page(self, index: int):
        pass  # Expandible para futuras páginas del panel

    def _logout(self):
        self._auth.logout()
        self.close()
        from ca_program.view.login_gui import LoginGUI
        self._login_window = LoginGUI(self._auth)
        self._login_window.show()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point independiente
# ──────────────────────────────────────────────────────────────────────────────

def run():
    app = QApplication(sys.argv)
    window = AdminGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
