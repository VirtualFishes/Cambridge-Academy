from ca_program.entities.user import User
from ca_program.entities.fixed_values import UserRole
from database.connection import get_connection


class UserModel:

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
