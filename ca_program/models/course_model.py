from ca_program.entities.course import Course
from ca_program.entities.fixed_values import UserRole
from ca_program.entities.professor import Professor
from ca_program.entities.student import Student
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
    def update_course(
        code_course: int | str,
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
        """
        Actualiza la información de un curso registrado.

        El código del curso se usa como identificador estable del registro y no
        se modifica. Los datos propios del curso se actualizan en la tabla
        courses, incluyendo el profesor asignado mediante id_professor.

        Retorna la entidad Course actualizada para que la capa de servicio y la
        GUI puedan refrescar la información sin ejecutar SQL adicional.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            current_course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=code_course,
            )

            if current_course is None:
                raise ValueError("El curso que intenta modificar no existe.")

            professor = CourseModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
            )

            if professor is None:
                raise ValueError("El profesor asignado no existe.")

            cursor.execute(
                """
                UPDATE courses
                SET
                    id_professor = %s,
                    name = %s,
                    description = %s,
                    price = %s,
                    duration_days = %s,
                    intensity_hours = %s,
                    schedule = %s,
                    location = %s,
                    start_date = %s,
                    end_date = %s
                WHERE code_course = %s;
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
                    code_course,
                ),
            )

            updated_course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=code_course,
            )

            if updated_course is None:
                raise ValueError("No fue posible recuperar el curso actualizado.")

            connection.commit()
            return updated_course

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    modify_course = update_course
    edit_course = update_course
    update = update_course

    @staticmethod
    def delete_course(code_course: int | str) -> Course:
        """
        Elimina permanentemente un curso y sus datos académicos asociados.

        La eliminación se realiza en una sola transacción para evitar registros
        huérfanos. El orden respeta las dependencias del modelo relacional:
        pagos, recibos, notas, matrículas y curso.

        No elimina al profesor ni a los estudiantes, porque esos registros
        pertenecen a entidades independientes del sistema.

        Retorna la entidad Course eliminada para que la capa de servicio pueda
        construir una respuesta clara sin ejecutar consultas adicionales.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=code_course,
            )

            if course is None:
                raise ValueError("El curso que intenta eliminar no existe.")

            cursor.execute(
                """
                DELETE FROM payments
                WHERE id_receipt IN (
                    SELECT r.id_receipt
                    FROM receipts r
                    INNER JOIN enrollments e ON r.id_enrollment = e.id_enrollment
                    WHERE e.code_course = %s
                );
                """,
                (code_course,),
            )

            cursor.execute(
                """
                DELETE FROM receipts
                WHERE id_enrollment IN (
                    SELECT id_enrollment
                    FROM enrollments
                    WHERE code_course = %s
                );
                """,
                (code_course,),
            )

            cursor.execute(
                """
                DELETE FROM grades
                WHERE id_enrollment IN (
                    SELECT id_enrollment
                    FROM enrollments
                    WHERE code_course = %s
                );
                """,
                (code_course,),
            )

            cursor.execute(
                """
                DELETE FROM enrollments
                WHERE code_course = %s;
                """,
                (code_course,),
            )

            cursor.execute(
                """
                DELETE FROM courses
                WHERE code_course = %s;
                """,
                (code_course,),
            )

            connection.commit()
            return course

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    remove_course = delete_course
    delete_by_code = delete_course
    delete_by_id = delete_course
    destroy_course = delete_course


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
    def get_students_by_course(code_course: int | str) -> list[Student]:
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
                FROM enrollments e
                INNER JOIN students s ON e.id_student = s.id_student
                INNER JOIN users u ON s.id_user = u.id_user
                WHERE e.code_course = %s
                ORDER BY u.name ASC, s.id_student ASC;
            """
            cursor.execute(query, (code_course,))
            results = cursor.fetchall()

            return [CourseModel._map_student_to_entity(row) for row in results]

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
    def course_exists(code_course: int | str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM courses
                WHERE code_course = %s
                LIMIT 1;
            """
            cursor.execute(query, (code_course,))
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

        if result is None:
            return None

        return CourseModel._map_professor_to_entity(result)

    @staticmethod
    def _map_to_entity(row: tuple) -> Course:
        (
            code_course,
            name,
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
            professor_name,
            professor_password,
            professor_role,
            professor_email,
            professor_birth_date,
            professor_nationality,
            enrolled_students,
        ) = row

        professor_user = User(
            id_user=id_user,
            name=professor_name,
            password=professor_password,
            role=UserRole(professor_role),
            email=professor_email,
            birth_date=professor_birth_date,
            nationality=professor_nationality,
        )

        professor = Professor(
            id_professor=id_professor,
            professional_title=professional_title,
            user=professor_user,
        )

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
        course.enrolled_students = int(enrolled_students or 0)

        return course

    @staticmethod
    def _map_professor_to_entity(row: tuple) -> Professor:
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

    @staticmethod
    def _map_student_to_entity(row: tuple) -> Student:
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
