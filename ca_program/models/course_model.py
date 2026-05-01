from ca_program.entities.course import Course
from ca_program.entities.fixed_values import UserRole
from ca_program.entities.professor import Professor
from ca_program.entities.user import User
from database.connection import get_connection


class CourseModel:

    @staticmethod
    def create_course(
        name: str,
        description: str,
        price: float,
        duration_days: int,
        intensity_hours: int,
        schedule: str,
        location: str,
        start_date,
        end_date,
        id_professor: str,
    ) -> Course:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            professor = CourseModel._get_professor_by_id_with_cursor(cursor, id_professor)

            if professor is None:
                raise ValueError("El profesor asignado no existe.")

            cursor.execute(
                """
                INSERT INTO courses (
                    id_professor,
                    name,
                    description,
                    price,
                    duration_days,
                    intensity_hours,
                    schedule,
                    location,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING code_course;
                """,
                (
                    id_professor,
                    name,
                    description,
                    price,
                    duration_days,
                    intensity_hours,
                    schedule,
                    location,
                    start_date,
                    end_date,
                ),
            )

            code_course = cursor.fetchone()[0]
            connection.commit()

            course = Course(
                code_course=code_course,
                name=name,
                description=description,
                price=float(price),
                duration_days=duration_days,
                intensity_hours=intensity_hours,
                schedule=schedule,
                location=location,
                start_date=start_date,
                end_date=end_date,
                professor=professor,
            )
            course.enrolled_students = 0

            return course

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_all_courses() -> list[Course]:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT
                    c.code_course,
                    c.name,
                    c.description,
                    c.price,
                    c.duration_days,
                    c.intensity_hours,
                    c.schedule,
                    c.location,
                    c.start_date,
                    c.end_date,
                    p.id_professor,
                    p.professional_title,
                    u.id_user,
                    u.name,
                    u.password,
                    u.role,
                    u.email,
                    u.birth_date,
                    u.nationality,
                    COUNT(e.id_enrollment) AS enrolled_students
                FROM courses c
                INNER JOIN professors p ON c.id_professor = p.id_professor
                INNER JOIN users u ON p.id_user = u.id_user
                LEFT JOIN enrollments e ON e.code_course = c.code_course
                GROUP BY
                    c.code_course,
                    c.name,
                    c.description,
                    c.price,
                    c.duration_days,
                    c.intensity_hours,
                    c.schedule,
                    c.location,
                    c.start_date,
                    c.end_date,
                    p.id_professor,
                    p.professional_title,
                    u.id_user,
                    u.name,
                    u.password,
                    u.role,
                    u.email,
                    u.birth_date,
                    u.nationality
                ORDER BY c.start_date DESC, c.name ASC;
            """
            cursor.execute(query)
            results = cursor.fetchall()

            return [CourseModel._map_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_course_by_code(code_course: int | str) -> Course | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=code_course,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def professor_exists(id_professor: str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM professors
                WHERE id_professor = %s
                LIMIT 1;
            """
            cursor.execute(query, (id_professor,))
            return cursor.fetchone() is not None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _get_course_by_code_with_cursor(cursor, code_course: int | str) -> Course | None:
        query = """
            SELECT
                c.code_course,
                c.name,
                c.description,
                c.price,
                c.duration_days,
                c.intensity_hours,
                c.schedule,
                c.location,
                c.start_date,
                c.end_date,
                p.id_professor,
                p.professional_title,
                u.id_user,
                u.name,
                u.password,
                u.role,
                u.email,
                u.birth_date,
                u.nationality,
                COUNT(e.id_enrollment) AS enrolled_students
            FROM courses c
            INNER JOIN professors p ON c.id_professor = p.id_professor
            INNER JOIN users u ON p.id_user = u.id_user
            LEFT JOIN enrollments e ON e.code_course = c.code_course
            WHERE c.code_course = %s
            GROUP BY
                c.code_course,
                c.name,
                c.description,
                c.price,
                c.duration_days,
                c.intensity_hours,
                c.schedule,
                c.location,
                c.start_date,
                c.end_date,
                p.id_professor,
                p.professional_title,
                u.id_user,
                u.name,
                u.password,
                u.role,
                u.email,
                u.birth_date,
                u.nationality;
        """
        cursor.execute(query, (code_course,))
        result = cursor.fetchone()

        if result:
            return CourseModel._map_to_entity(result)

        return None

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
            ) = result

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

        return None

    @staticmethod
    def _map_to_entity(row: tuple) -> Course:
        (
            code_course,
            course_name,
            description,
            price,
            duration_days,
            intensity_hours,
            schedule,
            location,
            start_date,
            end_date,
            id_professor,
            professional_title,
            id_user,
            user_name,
            password,
            role,
            email,
            birth_date,
            nationality,
            enrolled_students,
        ) = row

        user = User(
            id_user=id_user,
            name=user_name,
            password=password,
            role=UserRole(role),
            email=email,
            birth_date=birth_date,
            nationality=nationality,
        )

        professor = Professor(
            id_professor=id_professor,
            professional_title=professional_title,
            user=user,
        )

        course = Course(
            code_course=code_course,
            name=course_name,
            description=description,
            price=float(price),
            duration_days=duration_days,
            intensity_hours=intensity_hours,
            schedule=schedule,
            location=location,
            start_date=start_date,
            end_date=end_date,
            professor=professor,
        )
        course.enrolled_students = int(enrolled_students or 0)

        return course
