from ca_program.entities.fixed_values import UserRole
from ca_program.entities.professor import Professor
from ca_program.entities.user import User
from ca_program.models.user_model import UserModel
from database.connection import get_connection


class ProfessorModel:

    @staticmethod
    def create_professor(
        id_professor: str,
        name: str,
        password: str,
        email: str,
        birth_date,
        nationality: str,
        professional_title: str,
    ) -> Professor:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            user_created = UserModel.create_user(
                name=name,
                password=password,
                role=UserRole.PROFESSOR,
                email=email,
                birth_date=birth_date,
                nationality=nationality,
                cursor=cursor,
            )

            cursor.execute(
                """
                INSERT INTO professors (id_professor, id_user, professional_title)
                VALUES (%s, %s, %s);
                """,
                (id_professor, user_created.id_user, professional_title),
            )

            connection.commit()

            return Professor(
                id_professor=id_professor,
                professional_title=professional_title,
                user=user_created,
            )

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_all_professors() -> list[Professor]:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT
                    p.id_professor,
                    p.professional_title,
                    u.id_user,
                    u.name,
                    u.password,
                    u.role,
                    u.email,
                    u.birth_date,
                    u.nationality
                FROM professors p
                INNER JOIN users u ON p.id_user = u.id_user
                ORDER BY u.name ASC, p.id_professor ASC;
            """
            cursor.execute(query)
            results = cursor.fetchall()

            return [ProfessorModel._map_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_professor_by_id(id_professor: str) -> Professor | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def email_exists(email: str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1;
            """
            cursor.execute(query, (email,))
            return cursor.fetchone() is not None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _get_professor_by_id_with_cursor(cursor, id_professor: str) -> Professor | None:
        query = """
            SELECT
                p.id_professor,
                p.professional_title,
                u.id_user,
                u.name,
                u.password,
                u.role,
                u.email,
                u.birth_date,
                u.nationality
            FROM professors p
            INNER JOIN users u ON p.id_user = u.id_user
            WHERE p.id_professor = %s;
        """
        cursor.execute(query, (id_professor,))
        result = cursor.fetchone()

        if result:
            return ProfessorModel._map_to_entity(result)

        return None

    @staticmethod
    def _map_to_entity(row: tuple) -> Professor:
        (
            id_professor,
            professional_title,
            id_user,
            name,
            password,
            role,
            email,
            birth_date,
            nationality,
        ) = row

        user = User(
            id_user=id_user,
            name=name,
            password=password,
            role=UserRole(role),
            email=email,
            birth_date=birth_date,
            nationality=nationality,
        )

        return Professor(
            id_professor=id_professor,
            professional_title=professional_title,
            user=user,
        )
