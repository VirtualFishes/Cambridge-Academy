import psycopg2
from ca_program.entities.user import User
from database.connection import get_connection


class UserModel:
    """Modelo que gestiona las operaciones de base de datos para la entidad User."""

    def get_user_by_name(self, name: str) -> User | None:
        """Busca un usuario por nombre. Retorna User o None si no existe."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_user, name, password FROM users WHERE name = %s",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                user = User(id_user=row[0], name=row[1], password=row[2])
                user.role = self._get_role(conn, row[0])
                return user
            return None
        except psycopg2.Error as e:
            print(f"[UserModel] Error al consultar usuario: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, id_user: int) -> User | None:
        """Busca un usuario por ID."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_user, name, password FROM users WHERE id_user = %s",
                (id_user,)
            )
            row = cursor.fetchone()
            if row:
                user = User(id_user=row[0], name=row[1], password=row[2])
                user.role = self._get_role(conn, row[0])
                return user
            return None
        except psycopg2.Error as e:
            print(f"[UserModel] Error al consultar usuario por ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_users(self) -> list[User]:
        """Retorna todos los usuarios del sistema con su rol."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_user, name, password FROM users")
            rows = cursor.fetchall()
            users = []
            for row in rows:
                user = User(id_user=row[0], name=row[1], password=row[2])
                user.role = self._get_role(conn, row[0])
                users.append(user)
            return users
        except psycopg2.Error as e:
            print(f"[UserModel] Error al obtener usuarios: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def create_user(self, name: str, password: str) -> int | None:
        """Crea un nuevo usuario. Retorna el id_user generado o None si falla."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, password) VALUES (%s, %s) RETURNING id_user",
                (name, password)
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        except psycopg2.Error as e:
            print(f"[UserModel] Error al crear usuario: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def delete_user(self, id_user: int) -> bool:
        """Elimina un usuario por ID. Retorna True si fue exitoso."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id_user = %s", (id_user,))
            conn.commit()
            return cursor.rowcount > 0
        except psycopg2.Error as e:
            print(f"[UserModel] Error al eliminar usuario: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def _get_role(self, conn, id_user: int) -> str:
        """Determina el rol del usuario consultando las tablas relacionadas."""
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM administrators WHERE id_user = %s", (id_user,))
        if cursor.fetchone():
            return "admin"
        cursor.execute("SELECT 1 FROM professors WHERE id_user = %s", (id_user,))
        if cursor.fetchone():
            return "professor"
        cursor.execute("SELECT 1 FROM students WHERE id_user = %s", (id_user,))
        if cursor.fetchone():
            return "student"
        return "unknown"
