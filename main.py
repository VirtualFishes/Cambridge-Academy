"""
Punto de entrada principal del sistema ca_program.
Ejecutar con: python main.py
"""

import sys
from PySide6.QtWidgets import QApplication
from ca_program.views.admin_gui import AdminGUI


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CA Program")

    window = AdminGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
