"""
setup.py — Configura el entorno virtual, instala dependencias y prepara ejecución.

Ejecutar con:
    python setup.py

Luego ejecutar la aplicación con:
    run.bat
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / "venv"
VSCODE_DIR = PROJECT_ROOT / ".vscode"
VSCODE_SETTINGS = VSCODE_DIR / "settings.json"

DEPENDENCIES = [
    "psycopg2-binary",
    "PySide6",
]

REQUIRED_IMPORTS = [
    ("psycopg2", "psycopg2-binary"),
    ("PySide6", "PySide6"),
]


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Ejecuta un comando y detiene el setup si ocurre un error."""
    result = subprocess.run(command, **kwargs)

    if result.returncode != 0:
        print(f"\n❌ Error al ejecutar: {' '.join(command)}")
        sys.exit(result.returncode)

    return result


def get_venv_python() -> Path:
    """Retorna la ruta del Python dentro del entorno virtual."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


def is_dependency_installed(package_name: str) -> bool:
    """Verifica si un paquete está instalado dentro del entorno virtual."""
    python_path = get_venv_python()

    result = subprocess.run(
        [str(python_path), "-m", "pip", "show", package_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


def validate_python_version() -> None:
    """Advierte cuando se usa una versión de Python distinta a la recomendada."""
    major = sys.version_info.major
    minor = sys.version_info.minor

    print(f"\n🐍 Python detectado: {major}.{minor}.{sys.version_info.micro}")
    print(f"📍 Intérprete usado para crear el entorno: {sys.executable}")

    if major != 3 or minor < 10:
        print("\n❌ Este proyecto requiere Python 3.10 o superior.")
        sys.exit(1)

    if minor >= 13:
        print(
            "\n⚠️  Advertencia: estás usando Python 3.13.\n"
            "   El proyecto fue trabajado pensando en Python 3.10+ y se recomienda Python 3.11.\n"
            "   Puede funcionar, pero para mayor estabilidad se recomienda crear el entorno con Python 3.11."
        )


def create_virtual_environment() -> None:
    """Crea el entorno virtual si todavía no existe."""
    if VENV_DIR.is_dir():
        print(f"\n✅ Entorno virtual '{VENV_DIR.name}' ya existe.")
        return

    print(f"\n📦 Creando entorno virtual en '{VENV_DIR.name}'...")
    venv.create(str(VENV_DIR), with_pip=True)
    print("✅ Entorno virtual creado.")


def upgrade_pip() -> None:
    """Actualiza pip dentro del entorno virtual."""
    python_path = get_venv_python()

    print("\n⬆️  Actualizando pip...")
    run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
    print("✅ pip actualizado.")


def install_dependencies() -> None:
    """Instala las dependencias faltantes dentro del entorno virtual."""
    python_path = get_venv_python()

    print("\n📥 Verificando dependencias...\n")

    for dependency in DEPENDENCIES:
        if is_dependency_installed(dependency):
            print(f"  ✅ {dependency} ya instalado.")
            continue

        print(f"  ⬇️  Instalando {dependency}...")
        run([str(python_path), "-m", "pip", "install", dependency])
        print(f"  ✅ {dependency} instalado.")


def verify_imports() -> None:
    """Comprueba que las dependencias principales importen desde el venv."""
    python_path = get_venv_python()

    print("\n🧪 Verificando imports principales...\n")

    for import_name, package_name in REQUIRED_IMPORTS:
        result = subprocess.run(
            [
                str(python_path),
                "-c",
                f"import {import_name}; print('{package_name} OK')",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ No fue posible importar {import_name}.")
            print(result.stderr)
            sys.exit(result.returncode)

        print(f"  ✅ {result.stdout.strip()}")


def create_run_scripts() -> None:
    """Crea scripts para ejecutar la aplicación usando siempre el venv."""
    if sys.platform == "win32":
        run_file = PROJECT_ROOT / "run.bat"
        run_file.write_text(
            "@echo off\n"
            "cd /d %~dp0\n"
            "call venv\\Scripts\\activate\n"
            "python main.py\n"
            "pause\n",
            encoding="utf-8",
        )
        print("\n✅ Archivo run.bat creado.")
    else:
        run_file = PROJECT_ROOT / "run.sh"
        run_file.write_text(
            "#!/bin/bash\n"
            "cd \"$(dirname \"$0\")\"\n"
            "source venv/bin/activate\n"
            "python main.py\n",
            encoding="utf-8",
        )
        os.chmod(run_file, 0o755)
        print("\n✅ Archivo run.sh creado.")


def configure_vscode_interpreter() -> None:
    """Configura VS Code para usar el Python del entorno virtual del proyecto."""
    VSCODE_DIR.mkdir(exist_ok=True)

    settings = {}
    if VSCODE_SETTINGS.exists():
        try:
            settings = json.loads(VSCODE_SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings = {}

    if sys.platform == "win32":
        interpreter_path = "${workspaceFolder}\\venv\\Scripts\\python.exe"
    else:
        interpreter_path = "${workspaceFolder}/venv/bin/python"

    settings["python.defaultInterpreterPath"] = interpreter_path
    settings["python.terminal.activateEnvironment"] = True

    VSCODE_SETTINGS.write_text(
        json.dumps(settings, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print("✅ VS Code configurado para usar el entorno virtual del proyecto.")


def print_final_instructions() -> None:
    """Muestra instrucciones finales claras para ejecutar el sistema."""
    python_path = get_venv_python()

    print("\n" + "=" * 58)
    print("  ✅ Entorno listo.")
    print("=" * 58)

    print("\nPython correcto del proyecto:")
    print(f"  {python_path}")

    print("\nPara ejecutar la aplicación:")

    if sys.platform == "win32":
        print("  run.bat")
        print("\nO manualmente:")
        print("  .\\venv\\Scripts\\activate")
        print("  python main.py")
    else:
        print("  ./run.sh")
        print("\nO manualmente:")
        print("  source venv/bin/activate")
        print("  python main.py")

    print("\nVerificación del intérprete activo:")
    print('  python -c "import sys; print(sys.executable)"')

    print("\nDebe aparecer una ruta dentro de la carpeta:")
    print("  venv")


def main() -> None:
    print("=" * 58)
    print("  Cambridge Academy — Configuración del entorno")
    print("=" * 58)

    validate_python_version()
    create_virtual_environment()
    upgrade_pip()
    install_dependencies()
    verify_imports()
    create_run_scripts()
    configure_vscode_interpreter()
    print_final_instructions()


if __name__ == "__main__":
    main()
