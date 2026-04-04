"""
setup.py — Configura el entorno virtual e instala las dependencias del proyecto.
Ejecutar con: python setup.py
"""

import subprocess
import sys
import os
import venv

VENV_DIR = "venv"
DEPENDENCIES = [
    "psycopg2-binary",
    "PySide6",
]


def run(cmd, **kwargs):
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\n❌ Error al ejecutar: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return result


def get_venv_python():
    """Retorna la ruta al Python dentro del entorno virtual."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def get_venv_pip():
    """Retorna la ruta al pip dentro del entorno virtual."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    return os.path.join(VENV_DIR, "bin", "pip")


def is_dependency_installed(pip_path, package_name):
    """Verifica si un paquete ya está instalado en el entorno virtual."""
    result = subprocess.run(
        [pip_path, "show", package_name],
        capture_output=True
    )
    return result.returncode == 0


def main():
    print("=" * 50)
    print("  CA Program — Configuración del entorno")
    print("=" * 50)

    # ── 1. Crear entorno virtual si no existe ────────────────────────────────
    if os.path.isdir(VENV_DIR):
        print(f"\n✅ Entorno virtual '{VENV_DIR}' ya existe, omitiendo creación.")
    else:
        print(f"\n📦 Creando entorno virtual en '{VENV_DIR}'...")
        venv.create(VENV_DIR, with_pip=True)
        print("✅ Entorno virtual creado.")

    pip_path = get_venv_pip()
    python_path = get_venv_python()

    # ── 2. Actualizar pip ────────────────────────────────────────────────────
    print("\n⬆️  Actualizando pip...")
    run([python_path, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
    print("✅ pip actualizado.")

    # ── 3. Instalar dependencias (solo las que faltan) ───────────────────────
    print("\n📥 Verificando dependencias...\n")
    for dep in DEPENDENCIES:
        if is_dependency_installed(pip_path, dep):
            print(f"  ✅ {dep} ya instalado.")
        else:
            print(f"  ⬇️  Instalando {dep}...")
            run([pip_path, "install", dep])
            print(f"  ✅ {dep} instalado.")

    # ── 4. Instrucciones finales ─────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  ✅ Entorno listo.")
    print("=" * 50)
    print("\nPara ejecutar la aplicación:\n")

    if sys.platform == "win32":
        print(f"  .\\{VENV_DIR}\\Scripts\\activate")
    else:
        print(f"  source {VENV_DIR}/bin/activate")

    print("  python main.py\n")


if __name__ == "__main__":
    main()
