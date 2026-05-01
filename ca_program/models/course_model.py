"""
Modelo de persistencia para cursos.

Centraliza el SQL de cursos, profesor asignado y estudiantes inscritos. El
modelo valida datos estructurales, conserva transacciones coherentes y mapea
filas a entidades, sin asumir responsabilidades de la GUI o de servicios.
"""

from ca_program.entities.course import Course
from ca_program.entities.fixed_values import UserRole
from ca_program.entities.professor import Professor
from ca_program.entities.student import Student
from ca_program.models.model_utils import (
    build_user_entity,
    require_date_order,
    require_identifier,
    require_non_negative_number,
    require_positive_int,
    require_text,
)
from database.connection import get_connection


class CourseModel:
    """Acceso a datos de cursos y consultas asociadas por profesor/estudiante."""

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
        """Registra un curso nuevo y retorna la entidad creada."""
        course_data = CourseModel._clean_course_payload(
            name=name,
            description=description,
            price=price,
            duration_days=duration_days,
            intensity_hours=intensity_hours,
            schedule=schedule,
            location=location,
            start_date=start_date,
            end_date=end_date,
            id_professor=id_professor,
        )

        connection = get_connection()
        cursor = connection.cursor()

        try:
            professor = CourseModel._get_professor_by_id_with_cursor(cursor, course_data["id_professor"])

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
                    course_data["id_professor"],
                    course_data["name"],
                    course_data["description"],
                    course_data["price"],
                    course_data["duration_days"],
                    course_data["intensity_hours"],
                    course_data["schedule"],
                    course_data["location"],
                    course_data["start_date"],
                    course_data["end_date"],
                ),
            )

            code_course = cursor.fetchone()[0]
            connection.commit()

            course = Course(
                code_course=str(code_course),
                name=course_data["name"],
                description=course_data["description"],
                price=course_data["price"],
                duration_days=course_data["duration_days"],
                intensity_hours=course_data["intensity_hours"],
                schedule=course_data["schedule"],
                location=course_data["location"],
                start_date=course_data["start_date"],
                end_date=course_data["end_date"],
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
        se modifica. Retorna la entidad actualizada para que la capa superior
        refresque la vista sin repetir consultas.
        """
        clean_code_course = require_identifier(code_course, "Código del curso")
        course_data = CourseModel._clean_course_payload(
            name=name,
            description=description,
            price=price,
            duration_days=duration_days,
            intensity_hours=intensity_hours,
            schedule=schedule,
            location=location,
            start_date=start_date,
            end_date=end_date,
            id_professor=id_professor,
        )

        connection = get_connection()
        cursor = connection.cursor()

        try:
            current_course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
            )

            if current_course is None:
                raise ValueError("El curso que intenta modificar no existe.")

            professor = CourseModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=course_data["id_professor"],
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
                    course_data["id_professor"],
                    course_data["name"],
                    course_data["description"],
                    course_data["price"],
                    course_data["duration_days"],
                    course_data["intensity_hours"],
                    course_data["schedule"],
                    course_data["location"],
                    course_data["start_date"],
                    course_data["end_date"],
                    clean_code_course,
                ),
            )

            updated_course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
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
        Elimina permanentemente un curso y sus datos académicos dependientes.

        No elimina al profesor ni a los estudiantes, porque son entidades
        independientes del curso.
        """
        clean_code_course = require_identifier(code_course, "Código del curso")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            course = CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
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
                (clean_code_course,),
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
                (clean_code_course,),
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
                (clean_code_course,),
            )

            cursor.execute("DELETE FROM enrollments WHERE code_course = %s;", (clean_code_course,))
            cursor.execute("DELETE FROM courses WHERE code_course = %s;", (clean_code_course,))

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
        """Consulta todos los cursos con su profesor y cantidad de inscritos pagados."""
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {CourseModel._base_course_select_from()}
                {CourseModel._base_course_group_by()}
                ORDER BY c.start_date DESC, c.name ASC;
            """
            cursor.execute(query)
            results = cursor.fetchall()

            return [CourseModel._map_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_courses_by_professor_id(id_professor: int | str) -> list[Course]:
        """
        Consulta los cursos asignados a un profesor específico.

        Soporta HU-24 al restringir la consulta al docente autenticado.
        """
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return CourseModel._get_courses_by_professor_id_with_cursor(
                cursor=cursor,
                id_professor=clean_id_professor,
            )

        finally:
            cursor.close()
            connection.close()

    get_assigned_courses_by_professor_id = get_courses_by_professor_id
    get_courses_by_professor = get_courses_by_professor_id
    get_assigned_courses = get_courses_by_professor_id

    @staticmethod
    def get_course_by_code(code_course: int | str) -> Course | None:
        """Consulta un curso por código sin validar pertenencia a profesor."""
        clean_code_course = require_identifier(code_course, "Código del curso")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return CourseModel._get_course_by_code_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_course_by_code_and_professor_id(
        code_course: int | str,
        id_professor: int | str,
    ) -> Course | None:
        """
        Consulta el detalle de un curso validando su profesor asignado.

        Soporta HU-25, evitando exponer cursos de otros profesores.
        """
        clean_code_course = require_identifier(code_course, "Código del curso")
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return CourseModel._get_course_by_code_and_professor_id_with_cursor(
                cursor=cursor,
                code_course=clean_code_course,
                id_professor=clean_id_professor,
            )

        finally:
            cursor.close()
            connection.close()

    get_assigned_course_detail = get_course_by_code_and_professor_id
    get_assigned_course_by_code = get_course_by_code_and_professor_id
    get_course_detail_by_professor = get_course_by_code_and_professor_id

    @staticmethod
    def get_students_by_course(code_course: int | str) -> list[Student]:
        """Consulta estudiantes matriculados en un curso específico."""
        clean_code_course = require_identifier(code_course, "Código del curso")
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
            cursor.execute(query, (clean_code_course,))
            results = cursor.fetchall()

            return [CourseModel._map_student_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def professor_exists(id_professor: str) -> bool:
        """Verifica existencia de un profesor por identificación."""
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM professors
                WHERE id_professor = %s
                LIMIT 1;
            """
            cursor.execute(query, (clean_id_professor,))
            return cursor.fetchone() is not None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def course_exists(code_course: int | str) -> bool:
        """Verifica existencia de un curso por código."""
        clean_code_course = require_identifier(code_course, "Código del curso")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM courses
                WHERE code_course = %s
                LIMIT 1;
            """
            cursor.execute(query, (clean_code_course,))
            return cursor.fetchone() is not None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _get_courses_by_professor_id_with_cursor(cursor, id_professor: int | str) -> list[Course]:
        """Consulta interna de cursos asignados usando cursor activo."""
        query = f"""
            {CourseModel._base_course_select_from()}
            WHERE c.id_professor = %s
            {CourseModel._base_course_group_by()}
            ORDER BY c.start_date DESC, c.name ASC;
        """
        cursor.execute(query, (id_professor,))
        results = cursor.fetchall()

        return [CourseModel._map_to_entity(row) for row in results]

    @staticmethod
    def _get_course_by_code_and_professor_id_with_cursor(
        cursor,
        code_course: int | str,
        id_professor: int | str,
    ) -> Course | None:
        """Consulta interna de curso por código y profesor usando cursor activo."""
        query = f"""
            {CourseModel._base_course_select_from()}
            WHERE c.code_course = %s
              AND c.id_professor = %s
            {CourseModel._base_course_group_by()};
        """
        cursor.execute(query, (code_course, id_professor))
        result = cursor.fetchone()

        if result:
            return CourseModel._map_to_entity(result)

        return None

    @staticmethod
    def _get_course_by_code_with_cursor(cursor, code_course: int | str) -> Course | None:
        """Consulta interna de curso por código usando cursor activo."""
        query = f"""
            {CourseModel._base_course_select_from()}
            WHERE c.code_course = %s
            {CourseModel._base_course_group_by()};
        """
        cursor.execute(query, (code_course,))
        result = cursor.fetchone()

        if result:
            return CourseModel._map_to_entity(result)

        return None

    @staticmethod
    def _get_professor_by_id_with_cursor(cursor, id_professor: str) -> Professor | None:
        """Consulta interna de profesor por identificación usando cursor activo."""
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
    def _base_course_select_from() -> str:
        """Fragmento SELECT/FROM común para consultas de cursos."""
        return """
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
                COUNT(DISTINCT CASE WHEN r.status = 'paid' THEN e.id_enrollment END) AS enrolled_students
            FROM courses c
            INNER JOIN professors p ON c.id_professor = p.id_professor
            INNER JOIN users u ON p.id_user = u.id_user
            LEFT JOIN enrollments e ON e.code_course = c.code_course
            LEFT JOIN receipts r ON r.id_enrollment = e.id_enrollment
        """

    @staticmethod
    def _base_course_group_by() -> str:
        """GROUP BY compartido por las consultas basadas en _base_course_select_from."""
        return """
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
        """

    @staticmethod
    def _clean_course_payload(
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
    ) -> dict:
        """Normaliza y valida los datos básicos de un curso."""
        require_date_order(start_date, end_date, "Fecha de inicio", "Fecha de finalización")

        return {
            "name": require_text(name, "Nombre del curso"),
            "description": require_text(description, "Descripción"),
            "price": require_non_negative_number(price, "Precio"),
            "duration_days": require_positive_int(duration_days, "Duración en días"),
            "intensity_hours": require_positive_int(intensity_hours, "Intensidad horaria"),
            "schedule": require_text(schedule, "Horario"),
            "location": require_text(location, "Ubicación"),
            "start_date": start_date,
            "end_date": end_date,
            "id_professor": require_identifier(id_professor, "Identificación del profesor"),
        }

    @staticmethod
    def _map_to_entity(row: tuple) -> Course:
        """Mapea una fila de curso con profesor a entidad Course."""
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

        professor_user = build_user_entity(
            id_user=id_user,
            name=professor_name,
            password=professor_password,
            role=professor_role,
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
            code_course=str(code_course),
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
        """Mapea una fila JOIN professors-users a entidad Professor."""
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

        user = build_user_entity(
            id_user=id_user,
            name=name,
            password=password,
            role=role,
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
        """Mapea una fila JOIN students-users a entidad Student."""
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

        user = build_user_entity(
            id_user=id_user,
            name=name,
            password=password,
            role=UserRole(role),
            email=email,
            birth_date=birth_date,
            nationality=nationality,
        )

        return Student(id_student=id_student, user=user)
