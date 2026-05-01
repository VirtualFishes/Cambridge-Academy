"""
database.connection — Centraliza la conexión PostgreSQL del sistema académico.

Este módulo pertenece a la infraestructura de datos. Su única responsabilidad es
construir conexiones a la base de datos a partir de variables de entorno o de un
archivo local ``.env`` ubicado en la raíz del proyecto.

No contiene consultas SQL, reglas de negocio ni transacciones de aplicación; esas
responsabilidades pertenecen a los modelos y servicios respectivamente.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import psycopg2
from psycopg2.extensions import connection as PostgreSQLConnection


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
ENV_PATH: Final[Path] = PROJECT_ROOT / ".env"

_ENV_KEYS: Final[dict[str, str]] = {
    "host": "DB_HOST",
    "port": "DB_PORT",
    "database": "DB_NAME",
    "user": "DB_USER",
    "password": "DB_PASSWORD",
}


class DatabaseConfigurationError(ConnectionError):
    """Error causado por configuración incompleta o inválida de la base de datos."""


class DatabaseConnectionError(ConnectionError):
    """Error causado por fallos al abrir la conexión con PostgreSQL."""


def _load_env_file(path: Path = ENV_PATH) -> None:
    """
    Carga variables desde un archivo ``.env`` simple sin dependencias externas.

    El método respeta variables ya existentes en el entorno para permitir que un
    despliegue real sobrescriba la configuración local sin editar archivos.

    Formato soportado por línea::

        DB_HOST=localhost
        DB_PORT=5432
        DB_NAME=cambridge_academy
    """
    if not path.exists():
        return

    if not path.is_file():
        raise DatabaseConfigurationError(
            f"La ruta de configuración no es un archivo válido: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as env_file:
            for line_number, raw_line in enumerate(env_file, start=1):
                parsed = _parse_env_line(raw_line, line_number)
                if parsed is None:
                    continue

                key, value = parsed
                os.environ.setdefault(key, value)

    except OSError as exc:
        raise DatabaseConfigurationError(
            f"No fue posible leer el archivo de configuración: {path}"
        ) from exc


def _parse_env_line(raw_line: str, line_number: int) -> tuple[str, str] | None:
    """
    Interpreta una línea del archivo ``.env``.

    Retorna ``None`` para líneas vacías o comentarios. Si la línea no tiene el
    formato esperado, falla de forma explícita para que el error sea fácil de
    corregir durante la instalación del proyecto.
    """
    line = raw_line.strip()

    if not line or line.startswith("#"):
        return None

    if line.startswith("export "):
        line = line[len("export ") :].strip()

    if "=" not in line:
        raise DatabaseConfigurationError(
            f"Línea inválida en .env ({line_number}). Usa el formato CLAVE=valor."
        )

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")

    if not key:
        raise DatabaseConfigurationError(
            f"Línea inválida en .env ({line_number}). La clave no puede estar vacía."
        )

    return key, value


def _get_db_config() -> dict[str, str | int]:
    """
    Construye la configuración de conexión desde variables de entorno.

    ``psycopg2.connect`` acepta ``port`` como cadena, pero se valida como entero
    para detectar temprano errores de digitación en ``DB_PORT``.
    """
    config: dict[str, str | int] = {
        config_key: os.getenv(env_key, "").strip()
        for config_key, env_key in _ENV_KEYS.items()
    }

    missing_vars = [
        env_key
        for config_key, env_key in _ENV_KEYS.items()
        if not config[config_key]
    ]

    if missing_vars:
        missing = ", ".join(missing_vars)
        raise DatabaseConfigurationError(
            "Faltan variables de entorno para conectar con la base de datos: "
            f"{missing}. Crea un archivo .env en la raíz del proyecto tomando "
            "como referencia el archivo .env.example."
        )

    config["port"] = _parse_port(config["port"])
    return config


def _parse_port(value: str | int) -> int:
    """Valida y convierte el puerto de PostgreSQL a entero."""
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise DatabaseConfigurationError("DB_PORT debe ser un número entero válido.") from exc

    if port <= 0 or port > 65535:
        raise DatabaseConfigurationError("DB_PORT debe estar entre 1 y 65535.")

    return port


def get_connection() -> PostgreSQLConnection:
    """
    Retorna una conexión activa a PostgreSQL.

    La conexión se entrega abierta para que la capa que la solicita controle el
    ciclo de vida correspondiente: ``commit``, ``rollback`` y ``close``. Esto es
    importante para mantener transacciones completas desde los servicios.
    """
    _load_env_file()
    config = _get_db_config()

    try:
        return psycopg2.connect(**config)
    except psycopg2.Error as exc:
        raise DatabaseConnectionError(
            "No se pudo conectar a la base de datos. Verifica host, puerto, "
            "nombre de base de datos, usuario, contraseña y disponibilidad del servidor."
        ) from exc
