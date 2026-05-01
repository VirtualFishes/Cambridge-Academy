from ca_program.entities.fixed_values import UserRole
from ca_program.entities.student import Student
from ca_program.entities.user import User
from ca_program.models.user_model import UserModel
from database.connection import get_connection


class StudentModel:

    @staticmethod
    def create_student(
        id_student: str,
        name: str,
        password: str,
        email: str,
        birth_date,
        nationality: str,
    ) -> Student:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            user_created = UserModel.create_user(
                name=name,
                password=password,
                role=UserRole.STUDENT,
                email=email,
                birth_date=birth_date,
                nationality=nationality,
                cursor=cursor,
            )

            cursor.execute(
                """
                INSERT INTO students (id_student, id_user)
                VALUES (%s, %s);
                """,
                (id_student, user_created.id_user),
            )

            connection.commit()

            return Student(
                id_student=id_student,
                user=user_created,
            )

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_all_students() -> list[Student]:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT
                    s.id_student,
                    u.id_user,
                    u.name,
                    u.password,
                    u.role,
                    u.email,
                    u.birth_date,
                    u.nationality
                FROM students s
                INNER JOIN users u ON s.id_user = u.id_user
                ORDER BY u.name ASC, s.id_student ASC;
            """
            cursor.execute(query)
            results = cursor.fetchall()

            return [StudentModel._map_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_student_by_id(id_student: str) -> Student | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=id_student,
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
    def _get_student_by_id_with_cursor(cursor, id_student: str) -> Student | None:
        query = """
            SELECT
                s.id_student,
                u.id_user,
                u.name,
                u.password,
                u.role,
                u.email,
                u.birth_date,
                u.nationality
            FROM students s
            INNER JOIN users u ON s.id_user = u.id_user
            WHERE s.id_student = %s;
        """
        cursor.execute(query, (id_student,))
        result = cursor.fetchone()

        if result:
            return StudentModel._map_to_entity(result)

        return None

    @staticmethod
    def _map_to_entity(row: tuple) -> Student:
        (
            id_student,
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

        return Student(id_student=id_student, user=user)
