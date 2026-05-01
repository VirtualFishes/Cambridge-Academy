"""
Punto de entrada principal del sistema ca_program.
Ejecutar con: python main.py
"""

import sys
from PySide6.QtWidgets import QApplication
from ca_program.views.login_gui import LoginGUI


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CA Program")

    window = LoginGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
