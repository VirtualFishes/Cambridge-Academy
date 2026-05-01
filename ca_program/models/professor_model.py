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
        professional_title: str
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
        Actualiza la información de un profesor registrado.

        Los datos personales se actualizan en la tabla users porque el profesor
        está asociado a un usuario del sistema. Los datos propios del docente,
        como la identificación y el título profesional, se actualizan en la
        tabla professors.

        current_id_professor:
            Identificación actual del profesor en la base de datos.

        id_professor:
            Nueva identificación del profesor. Puede ser igual a la actual.

        password:
            Si llega None o cadena vacía, se conserva la contraseña actual.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            current_professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=current_id_professor,
            )

            if current_professor is None:
                raise ValueError("El profesor que intenta modificar no existe.")

            if (
                id_professor != current_id_professor
                and ProfessorModel._professor_id_exists_with_cursor(cursor, id_professor)
            ):
                raise ValueError("Ya existe un profesor con esa identificación.")

            if ProfessorModel._email_exists_for_other_user_with_cursor(
                cursor=cursor,
                email=email,
                id_user=current_professor.user.id_user,
            ):
                raise ValueError("Ya existe otro usuario registrado con ese correo electrónico.")

            clean_password = None if password is None else str(password).strip()

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
                        name,
                        clean_password,
                        email,
                        birth_date,
                        nationality,
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
                        name,
                        email,
                        birth_date,
                        nationality,
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
                (
                    id_professor,
                    professional_title,
                    current_id_professor,
                ),
            )

            updated_professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
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
        Elimina permanentemente un profesor.

        La eliminación se permite únicamente cuando el profesor no tiene cursos
        asociados. Los cursos son registros académicos independientes y no deben
        eliminarse automáticamente como consecuencia de borrar un profesor.

        Si el profesor no tiene cursos asignados, se elimina primero el registro
        de professors y después el usuario asociado en users, todo dentro de la
        misma transacción.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
            )

            if professor is None:
                raise ValueError("El profesor que intenta eliminar no existe.")

            assigned_courses = ProfessorModel._count_courses_by_professor_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
            )

            if assigned_courses > 0:
                raise ValueError(
                    "No se puede eliminar el profesor porque tiene cursos asignados. "
                    "Primero debe reasignar o eliminar esos cursos."
                )

            cursor.execute(
                """
                DELETE FROM professors
                WHERE id_professor = %s;
                """,
                (id_professor,),
            )

            cursor.execute(
                """
                DELETE FROM users
                WHERE id_user = %s;
                """,
                (professor.user.id_user,),
            )

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
            professor = ProfessorModel._get_professor_by_id_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
            )
            return professor

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_professor_by_user_id(id_user: int) -> Professor | None:
        """
        Obtiene el perfil de profesor asociado a un usuario del sistema.

        Este método permite transformar el User autenticado en LoginGUI en su
        entidad Professor correspondiente. Es la base para que el panel del
        profesor consulte únicamente la información académica asociada a su
        cuenta.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return ProfessorModel._get_professor_by_user_id_with_cursor(
                cursor=cursor,
                id_user=id_user,
            )

        finally:
            cursor.close()
            connection.close()

    get_by_user_id = get_professor_by_user_id
    find_by_user_id = get_professor_by_user_id

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
    def has_assigned_courses(id_professor: str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return ProfessorModel._count_courses_by_professor_with_cursor(
                cursor=cursor,
                id_professor=id_professor,
            ) > 0

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
    def _get_professor_by_user_id_with_cursor(cursor, id_user: int) -> Professor | None:
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
