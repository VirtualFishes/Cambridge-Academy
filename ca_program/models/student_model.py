"""
Modelo de persistencia para estudiantes.

Este componente administra operaciones sobre ``students`` y su usuario asociado
sin mezclar reglas de presentación. Las transacciones que crean, modifican o
eliminan estudiantes preservan la consistencia entre ``users`` y ``students``.
"""

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.student import Student
from ca_program.models.model_utils import (
    build_user_entity,
    require_identifier,
    require_positive_int,
    require_text,
    validate_email,
)
from ca_program.models.user_model import UserModel
from database.connection import get_connection


class StudentModel:
    """Acceso a datos de estudiantes y búsquedas administrativas."""

    @staticmethod
    def create_student(
        id_student: str,
        name: str,
        password: str,
        email: str,
        birth_date,
        nationality: str,
    ) -> Student:
        """Crea un estudiante junto con su usuario de rol STUDENT."""
        clean_id_student = require_identifier(id_student, "Identificación del estudiante")
        clean_name = require_text(name, "Nombre")
        clean_password = require_text(password, "Contraseña")
        clean_email = validate_email(email)
        clean_nationality = require_text(nationality, "Nacionalidad")

        connection = get_connection()
        cursor = connection.cursor()

        try:
            user_created = UserModel.create_user(
                name=clean_name,
                password=clean_password,
                role=UserRole.STUDENT,
                email=clean_email,
                birth_date=birth_date,
                nationality=clean_nationality,
                cursor=cursor,
            )

            cursor.execute(
                """
                INSERT INTO students (id_student, id_user)
                VALUES (%s, %s);
                """,
                (clean_id_student, user_created.id_user),
            )

            connection.commit()

            return Student(id_student=clean_id_student, user=user_created)

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_all_students() -> list[Student]:
        """Retorna todos los estudiantes registrados, ordenados para la GUI."""
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
        """Consulta un estudiante por su identificación académica."""
        clean_id_student = require_identifier(id_student, "Identificación del estudiante")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return StudentModel._get_student_by_id_with_cursor(cursor, clean_id_student)

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_student_by_user_id(id_user: int) -> Student | None:
        """
        Obtiene el perfil de estudiante asociado a un usuario autenticado.

        Permite transformar el ``User`` del login en la entidad ``Student`` que
        necesitan los servicios académicos del estudiante.
        """
        clean_id_user = require_positive_int(id_user, "ID de usuario")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return StudentModel._get_student_by_user_id_with_cursor(
                cursor=cursor,
                id_user=clean_id_user,
            )

        finally:
            cursor.close()
            connection.close()

    get_by_user_id = get_student_by_user_id
    find_by_user_id = get_student_by_user_id

    @staticmethod
    def get_student_by_id_with_cursor(cursor, id_student: str) -> Student | None:
        """Consulta un estudiante usando una transacción externa."""
        clean_id_student = require_identifier(id_student, "Identificación del estudiante")
        return StudentModel._get_student_by_id_with_cursor(
            cursor=cursor,
            id_student=clean_id_student,
        )

    @staticmethod
    def search_students(search_text: str | None = None) -> list[Student]:
        """
        Busca estudiantes por identificación, nombre o correo.

        Si no hay texto de búsqueda, retorna la lista completa ordenada. Esto
        evita duplicar SQL en vistas administrativas como consulta de notas.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return StudentModel._search_students_with_cursor(
                cursor=cursor,
                search_text=search_text,
            )

        finally:
            cursor.close()
            connection.close()

    search_students_for_admin = search_students
    get_students_for_admin_selection = search_students
    find_students = search_students

    @staticmethod
    def update_student(
        current_id_student: str,
        id_student: str,
        name: str,
        password: str | None,
        email: str,
        birth_date,
        nationality: str,
    ) -> Student:
        """
        Actualiza identificación y datos personales del estudiante.

        La contraseña se conserva cuando ``password`` llega como None o cadena
        vacía. Toda la operación se ejecuta en una sola transacción.
        """
        current_id = require_identifier(current_id_student, "Identificación actual")
        new_id = require_identifier(id_student, "Nueva identificación")
        clean_name = require_text(name, "Nombre")
        clean_email = validate_email(email)
        clean_nationality = require_text(nationality, "Nacionalidad")
        clean_password = None if password is None else str(password).strip()

        connection = get_connection()
        cursor = connection.cursor()

        try:
            current_student = StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=current_id,
            )

            if current_student is None:
                raise ValueError("El estudiante que intenta modificar no existe.")

            if new_id != current_id and StudentModel._student_id_exists_with_cursor(cursor, new_id):
                raise ValueError("Ya existe un estudiante con esa identificación.")

            if StudentModel._email_exists_for_other_user_with_cursor(
                cursor=cursor,
                email=clean_email,
                id_user=current_student.user.id_user,
            ):
                raise ValueError("Ya existe otro usuario registrado con ese correo electrónico.")

            if clean_password:
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        name = %s,
                        password = %s,
                        email = %s,
                        birth_date = %s,
                        nationality = %s
                    WHERE id_user = %s;
                    """,
                    (
                        clean_name,
                        clean_password,
                        clean_email,
                        birth_date,
                        clean_nationality,
                        current_student.user.id_user,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        name = %s,
                        email = %s,
                        birth_date = %s,
                        nationality = %s
                    WHERE id_user = %s;
                    """,
                    (
                        clean_name,
                        clean_email,
                        birth_date,
                        clean_nationality,
                        current_student.user.id_user,
                    ),
                )

            cursor.execute(
                """
                UPDATE students
                SET id_student = %s
                WHERE id_student = %s;
                """,
                (new_id, current_id),
            )

            updated_student = StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=new_id,
            )

            if updated_student is None:
                raise ValueError("No fue posible recuperar el estudiante actualizado.")

            connection.commit()
            return updated_student

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    modify_student = update_student
    edit_student = update_student
    update = update_student

    @staticmethod
    def delete_student(id_student: str) -> Student:
        """
        Elimina permanentemente un estudiante y sus registros dependientes.

        Se respeta el orden relacional: pagos, recibos, notas, matrículas,
        estudiante y usuario. Esto evita registros huérfanos.
        """
        clean_id_student = require_identifier(id_student, "Identificación del estudiante")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            student = StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=clean_id_student,
            )

            if student is None:
                raise ValueError("El estudiante que intenta eliminar no existe.")

            id_user = student.user.id_user

            cursor.execute(
                """
                DELETE FROM payments
                WHERE id_receipt IN (
                    SELECT r.id_receipt
                    FROM receipts r
                    INNER JOIN enrollments e ON r.id_enrollment = e.id_enrollment
                    WHERE e.id_student = %s
                );
                """,
                (clean_id_student,),
            )

            cursor.execute(
                """
                DELETE FROM receipts
                WHERE id_enrollment IN (
                    SELECT id_enrollment
                    FROM enrollments
                    WHERE id_student = %s
                );
                """,
                (clean_id_student,),
            )

            cursor.execute(
                """
                DELETE FROM grades
                WHERE id_enrollment IN (
                    SELECT id_enrollment
                    FROM enrollments
                    WHERE id_student = %s
                );
                """,
                (clean_id_student,),
            )

            cursor.execute("DELETE FROM enrollments WHERE id_student = %s;", (clean_id_student,))
            cursor.execute("DELETE FROM students WHERE id_student = %s;", (clean_id_student,))
            cursor.execute("DELETE FROM users WHERE id_user = %s;", (id_user,))

            connection.commit()
            return student

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    remove_student = delete_student
    delete_by_id = delete_student

    @staticmethod
    def email_exists(email: str) -> bool:
        """Verifica si un correo ya está registrado en users."""
        clean_email = validate_email(email)
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1;
            """
            cursor.execute(query, (clean_email,))
            return cursor.fetchone() is not None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def email_exists_for_other_student(email: str, id_student: str) -> bool:
        """Verifica duplicidad de correo excluyendo al estudiante indicado."""
        clean_email = validate_email(email)
        clean_id_student = require_identifier(id_student, "Identificación del estudiante")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            student = StudentModel._get_student_by_id_with_cursor(cursor, clean_id_student)

            if student is None:
                return StudentModel._email_exists_with_cursor(cursor, clean_email)

            return StudentModel._email_exists_for_other_user_with_cursor(
                cursor=cursor,
                email=clean_email,
                id_user=student.user.id_user,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _get_student_by_id_with_cursor(cursor, id_student: str) -> Student | None:
        """Consulta interna de estudiante por identificación usando cursor activo."""
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
    def _get_student_by_user_id_with_cursor(cursor, id_user: int) -> Student | None:
        """Consulta interna de estudiante por id_user y rol STUDENT."""
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
            WHERE s.id_user = %s
              AND u.role = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_user, UserRole.STUDENT.value))
        result = cursor.fetchone()

        if result:
            return StudentModel._map_to_entity(result)

        return None

    @staticmethod
    def _search_students_with_cursor(cursor, search_text: str | None = None) -> list[Student]:
        """Ejecuta búsqueda flexible de estudiantes con un cursor activo."""
        clean_search = "" if search_text is None else str(search_text).strip()

        base_query = """
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
            WHERE u.role = %s
        """

        params = [UserRole.STUDENT.value]

        if clean_search:
            base_query += """
              AND (
                    CAST(s.id_student AS TEXT) ILIKE %s
                 OR u.name ILIKE %s
                 OR u.email ILIKE %s
              )
            """
            pattern = f"%{clean_search}%"
            params.extend([pattern, pattern, pattern])

        base_query += """
            ORDER BY u.name ASC, s.id_student ASC;
        """

        cursor.execute(base_query, tuple(params))
        results = cursor.fetchall()

        return [StudentModel._map_to_entity(row) for row in results]

    @staticmethod
    def _student_id_exists_with_cursor(cursor, id_student: str) -> bool:
        """Indica si existe un estudiante con la identificación indicada."""
        query = """
            SELECT 1
            FROM students
            WHERE id_student = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_student,))
        return cursor.fetchone() is not None

    @staticmethod
    def _email_exists_with_cursor(cursor, email: str) -> bool:
        """Indica si un correo existe sin abrir una conexión adicional."""
        query = """
            SELECT 1
            FROM users
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1;
        """
        cursor.execute(query, (email,))
        return cursor.fetchone() is not None

    @staticmethod
    def _email_exists_for_other_user_with_cursor(cursor, email: str, id_user: int) -> bool:
        """Indica si el correo pertenece a otro usuario distinto al indicado."""
        query = """
            SELECT 1
            FROM users
            WHERE LOWER(email) = LOWER(%s)
              AND id_user <> %s
            LIMIT 1;
        """
        cursor.execute(query, (email, id_user))
        return cursor.fetchone() is not None

    @staticmethod
    def _map_to_entity(row: tuple) -> Student:
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
            role=role,
            email=email,
            birth_date=birth_date,
            nationality=nationality,
        )

        return Student(id_student=id_student, user=user)
