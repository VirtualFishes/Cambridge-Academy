from ca_program.entities.fixed_values import UserRole
from ca_program.entities.student import Student
from ca_program.entities.user import User
from database.connection import get_connection
from ca_program.models.user_model import UserModel

class StudentModel:

    @staticmethod
    def create_student(
        id_student: str,
        name: str,
        password: str,
        email: str,
        birth_date,
        nationality: str
    ) -> Student:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            user_created = UserModel.create_user(name, password, UserRole.STUDENT, email, birth_date, nationality, cursor)

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
                user=user_created
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

        finally:
            cursor.close()
            connection.close()

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
        Actualiza la información de un estudiante.

        La información personal se actualiza en la tabla users porque el
        estudiante está asociado a un usuario del sistema. La identificación
        estudiantil se actualiza en la tabla students.

        current_id_student:
            Identificación actual del estudiante en la base de datos.

        id_student:
            Nueva identificación del estudiante. Puede ser igual a la actual.

        password:
            Si llega None o cadena vacía, se conserva la contraseña actual.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            current_student = StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=current_id_student,
            )

            if current_student is None:
                raise ValueError("El estudiante que intenta modificar no existe.")

            if (
                id_student != current_id_student
                and StudentModel._student_id_exists_with_cursor(cursor, id_student)
            ):
                raise ValueError("Ya existe un estudiante con esa identificación.")

            if StudentModel._email_exists_for_other_user_with_cursor(
                cursor=cursor,
                email=email,
                id_user=current_student.user.id_user,
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
                        name,
                        email,
                        birth_date,
                        nationality,
                        current_student.user.id_user,
                    ),
                )

            cursor.execute(
                """
                UPDATE students
                SET id_student = %s
                WHERE id_student = %s;
                """,
                (id_student, current_id_student),
            )

            updated_student = StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=id_student,
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

    @staticmethod
    def delete_student(id_student: str) -> Student:
        """
        Elimina permanentemente un estudiante y todos sus datos asociados.

        La eliminación se realiza en una sola transacción para evitar registros
        huérfanos. El orden respeta las dependencias del modelo relacional:
        pagos, recibos, notas, matrículas, estudiante y usuario.

        Retorna la entidad Student eliminada para que la capa de servicio pueda
        construir una respuesta clara sin consultar nuevamente la base de datos.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            student = StudentModel._get_student_by_id_with_cursor(
                cursor=cursor,
                id_student=id_student,
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
                (id_student,),
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
                (id_student,),
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
                (id_student,),
            )

            cursor.execute(
                """
                DELETE FROM enrollments
                WHERE id_student = %s;
                """,
                (id_student,),
            )

            cursor.execute(
                """
                DELETE FROM students
                WHERE id_student = %s;
                """,
                (id_student,),
            )

            cursor.execute(
                """
                DELETE FROM users
                WHERE id_user = %s;
                """,
                (id_user,),
            )

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
    def email_exists_for_other_student(email: str, id_student: str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            student = StudentModel._get_student_by_id_with_cursor(cursor, id_student)

            if student is None:
                return StudentModel.email_exists(email)

            return StudentModel._email_exists_for_other_user_with_cursor(
                cursor=cursor,
                email=email,
                id_user=student.user.id_user,
            )

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
    def _student_id_exists_with_cursor(cursor, id_student: str) -> bool:
        query = """
            SELECT 1
            FROM students
            WHERE id_student = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_student,))
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
