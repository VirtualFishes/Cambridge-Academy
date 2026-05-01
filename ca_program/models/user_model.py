from ca_program.entities.user import User
from ca_program.entities.fixed_values import UserRole
from database.connection import get_connection


class UserModel:

    @staticmethod
    def create_user(
        name: str,
        password: str,
        role: UserRole,
        email: str,
        birth_date,
        nationality: str,
        cursor=None
    ) -> User:

        if cursor is None:
            connection = get_connection()
            cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                name, password, role, email, birth_date, nationality
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_user;
            """,
            (
                name,
                password,
                role.value,
                email,
                birth_date,
                nationality,
            ),
        )
        id_user = cursor.fetchone()[0]

        return User(
            id_user=id_user,
            name=name,
            password=password,
            role=role,
            email=email,
            birth_date=birth_date,
            nationality=nationality,
        )

    @staticmethod
    def get_user_by_name(name: str) -> User | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT id_user, name, password, role, email, birth_date, nationality
                FROM users
                WHERE name = %s;
            """
            cursor.execute(query, (name,))
            result = cursor.fetchone()

            if result:
                return UserModel._map_to_entity(result)

            return None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def validate_password(user: User, password: str) -> bool:
        return user.password == password

    @staticmethod
    def get_user_by_id(id_user: int) -> User | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT id_user, name, password, role, email, birth_date, nationality
                FROM users
                WHERE id_user = %s;
            """
            cursor.execute(query, (id_user,))
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

        Si recibe un cursor externo, la operación queda bajo la transacción
        de quien lo invoca. Si no recibe cursor, abre y cierra su propia
        conexión.
        """
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
            cursor.execute(query, (new_password, id_user))
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
        id_user, name, password, role, email, birth_date, nationality = row

        return User(
            id_user=id_user,
            name=name,
            password=password,
            role=UserRole(role),
            email=email,
            birth_date=birth_date,
            nationality=nationality
        )
