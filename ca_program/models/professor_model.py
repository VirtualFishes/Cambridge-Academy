"""
Modelo de persistencia para profesores.

Gestiona la tabla ``professors`` y su vínculo con ``users``. Mantiene las
operaciones transaccionales necesarias para crear, modificar, consultar y
eliminar profesores sin trasladar lógica de interfaz a la capa de datos.
"""

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.professor import Professor
from ca_program.models.model_utils import (
    build_user_entity,
    require_identifier,
    require_positive_int,
    require_text,
    validate_email,
)
from ca_program.models.user_model import UserModel
from database.connection import get_connection


class ProfessorModel:
    """Acceso a datos de profesores y validaciones de persistencia."""

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
        """Crea un profesor junto con su usuario de rol PROFESSOR."""
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        clean_name = require_text(name, "Nombre")
        clean_password = require_text(password, "Contraseña")
        clean_email = validate_email(email)
        clean_nationality = require_text(nationality, "Nacionalidad")
        clean_professional_title = require_text(professional_title, "Título profesional")

        connection = get_connection()
        cursor = connection.cursor()

        try:
            user_created = UserModel.create_user(
                name=clean_name,
                password=clean_password,
                role=UserRole.PROFESSOR,
                email=clean_email,
                birth_date=birth_date,
                nationality=clean_nationality,
                cursor=cursor,
            )

            cursor.execute(
                """
                INSERT INTO professors (id_professor, id_user, professional_title)
                VALUES (%s, %s, %s);
                """,
                (clean_id_professor, user_created.id_user, clean_professional_title),
            )

            connection.commit()

            return Professor(
                id_professor=clean_id_professor,
                professional_title=clean_professional_title,
                user=user_created,
            )

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def update_professor(
        current_id_professor: str,
        id_professor: str,
        name: str,
        password: str | None,
        email: str,
        birth_date,
        nationality: str,
        professional_title: str,
    ) -> Professor:
        """
        Actualiza identificación, datos de usuario y título profesional.

        La contraseña se conserva cuando ``password`` llega vacío o None. La
        operación completa se confirma o revierte como una sola transacción.
        """
        current_id = require_identifier(current_id_professor, "Identificación actual")
        new_id = require_identifier(id_professor, "Nueva identificación")
        clean_name = require_text(name, "Nombre")
        clean_email = validate_email(email)
        clean_nationality = require_text(nationality, "Nacionalidad")
        clean_professional_title = require_text(professional_title, "Título profesional")
        clean_password = None if password is None else str(password).strip()

        connection = get_connection()
        cursor = connection.cursor()

        try:
            current_professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=current_id,
            )

            if current_professor is None:
                raise ValueError("El profesor que intenta modificar no existe.")

            if new_id != current_id and ProfessorModel._professor_id_exists_with_cursor(cursor, new_id):
                raise ValueError("Ya existe un profesor con esa identificación.")

            if ProfessorModel._email_exists_for_other_user_with_cursor(
                cursor=cursor,
                email=clean_email,
                id_user=current_professor.user.id_user,
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
                        current_professor.user.id_user,
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
                        current_professor.user.id_user,
                    ),
                )

            cursor.execute(
                """
                UPDATE professors
                SET
                    id_professor = %s,
                    professional_title = %s
                WHERE id_professor = %s;
                """,
                (new_id, clean_professional_title, current_id),
            )

            updated_professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=new_id,
            )

            if updated_professor is None:
                raise ValueError("No fue posible recuperar el profesor actualizado.")

            connection.commit()
            return updated_professor

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    modify_professor = update_professor
    edit_professor = update_professor
    update = update_professor
    save_professor_changes = update_professor

    @staticmethod
    def delete_professor(id_professor: str) -> Professor:
        """
        Elimina un profesor solo si no tiene cursos asignados.

        No se eliminan cursos en cascada porque son registros académicos
        independientes. Antes de borrar, el usuario administrativo debe
        reasignar o eliminar esos cursos desde su propio módulo.
        """
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=clean_id_professor,
            )

            if professor is None:
                raise ValueError("El profesor que intenta eliminar no existe.")

            assigned_courses = ProfessorModel._count_courses_by_professor_with_cursor(
                cursor=cursor,
                id_professor=clean_id_professor,
            )

            if assigned_courses > 0:
                raise ValueError(
                    "No se puede eliminar el profesor porque tiene cursos asignados. "
                    "Primero debe reasignar o eliminar esos cursos."
                )

            cursor.execute("DELETE FROM professors WHERE id_professor = %s;", (clean_id_professor,))
            cursor.execute("DELETE FROM users WHERE id_user = %s;", (professor.user.id_user,))

            connection.commit()
            return professor

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    remove_professor = delete_professor
    delete_by_id = delete_professor
    destroy_professor = delete_professor

    @staticmethod
    def get_all_professors() -> list[Professor]:
        """Retorna todos los profesores registrados para selección administrativa."""
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
        """Consulta un profesor por su identificación."""
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=clean_id_professor,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_professor_by_user_id(id_user: int) -> Professor | None:
        """Obtiene el perfil de profesor asociado a un usuario autenticado."""
        clean_id_user = require_positive_int(id_user, "ID de usuario")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return ProfessorModel._get_professor_by_user_id_with_cursor(
                cursor=cursor,
                id_user=clean_id_user,
            )

        finally:
            cursor.close()
            connection.close()

    get_by_user_id = get_professor_by_user_id
    find_by_user_id = get_professor_by_user_id

    @staticmethod
    def email_exists(email: str) -> bool:
        """Verifica si un correo ya existe en la tabla users."""
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
    def has_assigned_courses(id_professor: str) -> bool:
        """Indica si un profesor tiene cursos registrados a su nombre."""
        clean_id_professor = require_identifier(id_professor, "Identificación del profesor")
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return ProfessorModel._count_courses_by_professor_with_cursor(
                cursor=cursor,
                id_professor=clean_id_professor,
            ) > 0

        finally:
            cursor.close()
            connection.close()

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

        if result:
            return ProfessorModel._map_to_entity(result)

        return None

    @staticmethod
    def _get_professor_by_user_id_with_cursor(cursor, id_user: int) -> Professor | None:
        """Consulta interna de profesor por id_user y rol PROFESSOR."""
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
            WHERE p.id_user = %s
              AND u.role = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_user, UserRole.PROFESSOR.value))
        result = cursor.fetchone()

        if result:
            return ProfessorModel._map_to_entity(result)

        return None

    @staticmethod
    def _professor_id_exists_with_cursor(cursor, id_professor: str) -> bool:
        """Indica si ya existe un profesor con la identificación suministrada."""
        query = """
            SELECT 1
            FROM professors
            WHERE id_professor = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_professor,))
        return cursor.fetchone() is not None

    @staticmethod
    def _email_exists_for_other_user_with_cursor(cursor, email: str, id_user: int) -> bool:
        """Indica si el correo pertenece a un usuario distinto al indicado."""
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
    def _count_courses_by_professor_with_cursor(cursor, id_professor: str) -> int:
        """Cuenta cursos asignados a un profesor sin abrir otra conexión."""
        query = """
            SELECT COUNT(*)
            FROM courses
            WHERE id_professor = %s;
        """
        cursor.execute(query, (id_professor,))
        result = cursor.fetchone()
        return int(result[0] or 0)

    @staticmethod
    def _map_to_entity(row: tuple) -> Professor:
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
