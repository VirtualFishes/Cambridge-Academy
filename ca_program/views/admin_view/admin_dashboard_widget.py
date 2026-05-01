from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class AdminDashboardWidget(QWidget):
    def __init__(self, navigate: Callable[[str], None] | None = None, parent=None):
        super().__init__(parent)
        self.navigate = navigate
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("Panel administrativo")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Bienvenido al panel administrativo de Cambridge Academy. "
            "Desde aquí puedes gestionar la información académica principal."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)
        root.addLayout(grid)

        cards = [
            (
                "Estudiantes",
                "Gestión académica",
                "Registra y consulta la información básica de los estudiantes.",
                "students",
            ),
            (
                "Cursos",
                "Oferta académica",
                "Registra cursos, horarios, fechas, precios y profesor asignado.",
                "courses",
            ),
            (
                "Profesores",
                "Equipo docente",
                "Registra y consulta la información del personal docente.",
                "professors",
            ),
        ]

        for index, (title_text, tag, body, key) in enumerate(cards):
            grid.addWidget(self._make_card(title_text, tag, body, key), index // 2, index % 2)

        root.addStretch()

    def _make_card(self, title_text: str, tag: str, body: str, key: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        tag_label = QLabel(tag)
        tag_label.setObjectName("tagLabel")
        tag_label.setAlignment(Qt.AlignLeft)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        desc = QLabel(body)
        desc.setObjectName("cardText")
        desc.setWordWrap(True)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button = QPushButton("Abrir")
        button.setObjectName("secondaryButton")
        if self.navigate:
            button.clicked.connect(lambda checked=False, view_key=key: self.navigate(view_key))
        button_row.addWidget(button)

        layout.addWidget(tag_label)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addLayout(button_row)
        return card
