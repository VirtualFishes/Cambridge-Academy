"""
database/connection.py — Centraliza la conexión con la base de datos.

La configuración se lee desde variables de entorno o desde un archivo local .env
ubicado en la raíz del proyecto. El archivo .env no debe versionarse.
"""

import os
from pathlib import Path

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


_ENV_KEYS = {
    "host": "DB_HOST",
    "port": "DB_PORT",
    "database": "DB_NAME",
    "user": "DB_USER",
    "password": "DB_PASSWORD",
}


def _load_env_file(path: Path = ENV_PATH) -> None:
    """
    Carga variables desde un archivo .env simple sin agregar dependencias externas.

    Formato esperado por línea:
    DB_HOST=valor
    DB_PORT=valor
    """
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key:
                os.environ.setdefault(key, value)


def _get_db_config() -> dict:
    """Construye la configuración de conexión desde variables de entorno."""
    config = {config_key: os.getenv(env_key) for config_key, env_key in _ENV_KEYS.items()}

    missing_vars = [env_key for config_key, env_key in _ENV_KEYS.items() if not config[config_key]]
    if missing_vars:
        missing = ", ".join(missing_vars)
        raise ConnectionError(
            "Faltan variables de entorno para conectar con la base de datos: "
            f"{missing}. Crea un archivo .env en la raíz del proyecto tomando "
            "como referencia el archivo .env.example."
        )

    return config


def get_connection():
    """Retorna una conexión activa a la base de datos."""
    _load_env_file()

    try:
        return psycopg2.connect(**_get_db_config())
    except psycopg2.Error as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}") from e
