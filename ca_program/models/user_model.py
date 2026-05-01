"""
Modelo de persistencia para usuarios del sistema.

La clase centraliza operaciones CRUD parciales sobre la tabla ``users`` y
mapea filas de base de datos a entidades ``User``. No decide navegación,
permisos de pantalla ni reglas propias de cada rol; esas responsabilidades
pertenecen a services y views.
"""

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.user import User
from ca_program.models.model_utils import (
    build_user_entity,
    normalize_enum,
    require_positive_int,
    require_text,
    validate_email,
)
from database.connection import get_connection


class UserModel:
    """Acceso a datos de usuarios autenticables de Cambridge Academy."""

    @staticmethod
    def create_user(
        name: str,
        password: str,
        role: UserRole | str,
        email: str,
        birth_date,
        nationality: str,
        cursor=None,
    ) -> User:
        """
        Crea un usuario y retorna su entidad.

        Si recibe un cursor externo, no confirma ni revierte la transacción,
        porque el flujo completo lo controla el modelo/servicio que invoca. Si
        no recibe cursor, abre una conexión propia y confirma la operación.
        """
        clean_name = require_text(name, "Nombre")
        clean_password = require_text(password, "Contraseña")
        clean_role = normalize_enum(role, UserRole, "Rol")
        clean_email = validate_email(email)
        clean_nationality = require_text(nationality, "Nacionalidad")

        owns_connection = cursor is None
        connection = None

        if owns_connection:
            connection = get_connection()
            cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (
                    name, password, role, email, birth_date, nationality
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_user;
                """,
                (
                    clean_name,
                    clean_password,
                    clean_role.value,
                    clean_email,
                    birth_date,
                    clean_nationality,
                ),
            )
            id_user = cursor.fetchone()[0]

            if owns_connection:
                connection.commit()

            return User(
                id_user=id_user,
                name=clean_name,
                password=clean_password,
                role=clean_role,
                email=clean_email,
                birth_date=birth_date,
                nationality=clean_nationality,
            )

        except Exception:
            if owns_connection and connection:
                connection.rollback()
            raise

        finally:
            if owns_connection:
                cursor.close()
                connection.close()

    @staticmethod
    def get_user_by_name(name: str) -> User | None:
        """Consulta un usuario por nombre exacto de acceso."""
        clean_name = require_text(name, "Nombre")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT id_user, name, password, role, email, birth_date, nationality
                FROM users
                WHERE name = %s;
            """
            cursor.execute(query, (clean_name,))
            result = cursor.fetchone()

            if result:
                return UserModel._map_to_entity(result)

            return None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def validate_password(user: User | None, password: str) -> bool:
        """
        Compara la contraseña enviada con la almacenada en la entidad.

        El sistema actual conserva contraseñas en texto plano por compatibilidad
        con el proyecto existente. Cuando se agregue hashing, el cambio debe
        quedar encapsulado aquí y en la creación/actualización de usuarios.
        """
        if user is None:
            return False

        return user.password == str(password)

    @staticmethod
    def get_user_by_id(id_user: int) -> User | None:
        """Consulta un usuario por su identificador interno."""
        clean_id_user = require_positive_int(id_user, "ID de usuario")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT id_user, name, password, role, email, birth_date, nationality
                FROM users
                WHERE id_user = %s;
            """
            cursor.execute(query, (clean_id_user,))
            result = cursor.fetchone()

            if result:
                return UserModel._map_to_entity(result)

            return None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def update_password(id_user: int, new_password: str, cursor=None) -> bool:
        """
        Actualiza la contraseña de un usuario existente.

        Soporta cursor externo para integrarse a transacciones mayores, por
        ejemplo el cambio de contraseña desde un servicio autenticado.
        """
        clean_id_user = require_positive_int(id_user, "ID de usuario")
        clean_password = require_text(new_password, "Nueva contraseña")
        owns_connection = cursor is None
        connection = None

        if owns_connection:
            connection = get_connection()
            cursor = connection.cursor()

        try:
            query = """
                UPDATE users
                SET password = %s
                WHERE id_user = %s;
            """
            cursor.execute(query, (clean_password, clean_id_user))
            updated = cursor.rowcount > 0

            if owns_connection:
                connection.commit()

            return updated

        except Exception:
            if owns_connection and connection:
                connection.rollback()
            raise

        finally:
            if owns_connection:
                cursor.close()
                connection.close()

    @staticmethod
    def _map_to_entity(row: tuple) -> User:
        """Mapea una fila de ``users`` a la entidad ``User``."""
        id_user, name, password, role, email, birth_date, nationality = row

        return build_user_entity(
            id_user=id_user,
            name=name,
            password=password,
            role=role,
            email=email,
            birth_date=birth_date,
            nationality=nationality,
        )
