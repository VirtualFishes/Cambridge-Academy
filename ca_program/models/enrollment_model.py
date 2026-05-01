from datetime import date

from ca_program.entities.course import Course
from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import ReceiptStatus, UserRole
from ca_program.entities.professor import Professor
from ca_program.entities.student import Student
from ca_program.entities.user import User
from database.connection import get_connection


class EnrollmentModel:
    """Modelo de datos para matrículas de estudiantes en cursos."""

    STATUS_NOT_ENROLLED = "NO_INSCRITO"
    STATUS_PENDING_PAYMENT = "PENDIENTE_DE_PAGO"
    STATUS_ENROLLED = "INSCRITO"
    STATUS_EXPIRED = "VENCIDO"

    @staticmethod
    def create_enrollment(cursor, id_student: str, code_course: int | str) -> Enrollment:
        """
        Crea una matrícula usando el cursor de una transacción externa.

        No realiza commit ni rollback. En HU-21 esta operación forma parte del
        flujo de inscripción junto con la generación del recibo pendiente.
        """
        query = """
            INSERT INTO enrollments (id_student, code_course)
            VALUES (%s, %s)
            RETURNING id_enrollment;
        """
        cursor.execute(query, (id_student, code_course))
        id_enrollment = cursor.fetchone()[0]

        enrollment = EnrollmentModel.get_enrollment_by_id(
            cursor=cursor,
            id_enrollment=id_enrollment,
        )

        if enrollment is None:
            raise ValueError("No fue posible recuperar la inscripción creada.")

        return enrollment

    @staticmethod
    def delete_enrollment_by_id(cursor, id_enrollment: int) -> bool:
        """
        Elimina permanentemente una matrícula usando un cursor transaccional.

        Esta operación se usará principalmente cuando un recibo pendiente haya
        vencido y el estudiante quiera intentar nuevamente la inscripción.
        """
        query = """
            DELETE FROM enrollments
            WHERE id_enrollment = %s;
        """
        cursor.execute(query, (id_enrollment,))
        return cursor.rowcount > 0

    @staticmethod
    def get_enrollment_by_id(cursor, id_enrollment: int) -> Enrollment | None:
        """Consulta una matrícula por su identificador con un cursor existente."""
        query = f"""
            {EnrollmentModel._base_enrollment_select_from()}
            WHERE e.id_enrollment = %s
            {EnrollmentModel._base_enrollment_group_by()}
            LIMIT 1;
        """
        cursor.execute(query, (id_enrollment,))
        result = cursor.fetchone()

        if result:
            return EnrollmentModel._map_enrollment_to_entity(result)

        return None

    @staticmethod
    def get_enrollment_by_student_and_course(
        cursor,
        id_user: int | str,
        code_course: int | str,
    ) -> Enrollment | None:
        """
        Consulta la matrícula más reciente de un usuario estudiante en un curso.

        Retorna matrículas pendientes o pagadas. La capa de servicio decide qué
        hacer según el recibo asociado.
        """
        query = f"""
            {EnrollmentModel._base_enrollment_select_from()}
            WHERE student_user.id_user = %s
              AND c.code_course = %s
            {EnrollmentModel._base_enrollment_group_by()}
            ORDER BY e.id_enrollment DESC
            LIMIT 1;
        """
        cursor.execute(query, (id_user, code_course))
        result = cursor.fetchone()

        if result:
            return EnrollmentModel._map_enrollment_to_entity(result)

        return None

    @staticmethod
    def get_enrollments_by_student_user_id(id_user: int | str) -> list[Enrollment]:
        """
        Consulta las matrículas confirmadas de un usuario estudiante.

        Para HU-19, un curso solo se considera inscrito cuando su recibo está
        pagado. Las matrículas con recibo pendiente no se muestran como cursos
        inscritos confirmados.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {EnrollmentModel._base_enrollment_select_from(confirmed_only=True)}
                WHERE s.id_user = %s
                {EnrollmentModel._base_enrollment_group_by()}
                ORDER BY c.name ASC, e.id_enrollment ASC;
            """
            cursor.execute(query, (id_user,))
            results = cursor.fetchall()

            return [EnrollmentModel._map_enrollment_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_enrollments_by_student_id(id_student: str) -> list[Enrollment]:
        """
        Consulta las matrículas confirmadas asociadas a un estudiante.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {EnrollmentModel._base_enrollment_select_from(confirmed_only=True)}
                WHERE s.id_student = %s
                {EnrollmentModel._base_enrollment_group_by()}
                ORDER BY c.name ASC, e.id_enrollment ASC;
            """
            cursor.execute(query, (id_student,))
            results = cursor.fetchall()

            return [EnrollmentModel._map_enrollment_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_confirmed_enrollments_by_course_and_professor_id(
        code_course: int | str,
        id_professor: int | str,
    ) -> list[Enrollment]:
        """
        Consulta las matrículas confirmadas de un curso asignado a un profesor.

        Este método sirve como base para HU-26: registrar notas únicamente a
        estudiantes que pertenecen al curso del profesor autenticado y cuya
        inscripción ya fue confirmada mediante recibo pagado.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return EnrollmentModel.get_confirmed_enrollments_by_course_and_professor_id_with_cursor(
                cursor=cursor,
                code_course=code_course,
                id_professor=id_professor,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_confirmed_enrollments_by_course_and_professor_id_with_cursor(
        cursor,
        code_course: int | str,
        id_professor: int | str,
    ) -> list[Enrollment]:
        """
        Consulta matrículas confirmadas usando un cursor externo.

        El filtro por profesor evita exponer estudiantes de cursos que no
        pertenecen al docente autenticado. El filtro por recibo pagado conserva
        la regla de negocio de inscripción confirmada.
        """
        query = f"""
            {EnrollmentModel._base_enrollment_select_from(confirmed_only=True)}
            WHERE c.code_course = %s
              AND c.id_professor = %s
            {EnrollmentModel._base_enrollment_group_by()}
            ORDER BY student_user.name ASC, s.id_student ASC, e.id_enrollment ASC;
        """
        cursor.execute(query, (code_course, id_professor))
        results = cursor.fetchall()

        return [EnrollmentModel._map_enrollment_to_entity(row) for row in results]

    @staticmethod
    def get_confirmed_enrollment_by_id_course_and_professor_id(
        cursor,
        id_enrollment: int | str,
        code_course: int | str,
        id_professor: int | str,
    ) -> Enrollment | None:
        """
        Consulta una matrícula confirmada específica de un curso del profesor.

        Este método permite que la capa de servicio valide, antes de registrar
        notas, que la matrícula enviada desde la GUI realmente pertenece al
        curso seleccionado y al profesor autenticado.
        """
        query = f"""
            {EnrollmentModel._base_enrollment_select_from(confirmed_only=True)}
            WHERE e.id_enrollment = %s
              AND c.code_course = %s
              AND c.id_professor = %s
            {EnrollmentModel._base_enrollment_group_by()}
            LIMIT 1;
        """
        cursor.execute(query, (id_enrollment, code_course, id_professor))
        result = cursor.fetchone()

        if result:
            return EnrollmentModel._map_enrollment_to_entity(result)

        return None

    get_confirmed_enrollments_for_grading = get_confirmed_enrollments_by_course_and_professor_id
    get_gradable_enrollments_by_course_and_professor_id = get_confirmed_enrollments_by_course_and_professor_id
    get_confirmed_enrollment_for_grading = get_confirmed_enrollment_by_id_course_and_professor_id
    get_gradable_enrollment_by_id = get_confirmed_enrollment_by_id_course_and_professor_id

    @staticmethod
    def get_enrolled_courses_by_student_user_id(id_user: int | str) -> list[Course]:
        """
        Retorna únicamente los cursos inscritos y confirmados por pago.
        """
        enrollments = EnrollmentModel.get_enrollments_by_student_user_id(id_user)
        return [enrollment.course for enrollment in enrollments]

    @staticmethod
    def get_enrolled_courses_by_student_id(id_student: str) -> list[Course]:
        """
        Retorna únicamente los cursos inscritos y confirmados por pago.
        """
        enrollments = EnrollmentModel.get_enrollments_by_student_id(id_student)
        return [enrollment.course for enrollment in enrollments]

    @staticmethod
    def get_student_by_user_id(id_user: int | str) -> Student | None:
        """Obtiene el estudiante asociado a un usuario del sistema."""
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return EnrollmentModel.get_student_by_user_id_with_cursor(
                cursor=cursor,
                id_user=id_user,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_student_by_user_id_with_cursor(cursor, id_user: int | str) -> Student | None:
        """Obtiene el estudiante asociado a un usuario usando un cursor externo."""
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
            WHERE s.id_user = %s;
        """
        cursor.execute(query, (id_user,))
        result = cursor.fetchone()

        if result:
            return EnrollmentModel._map_student_to_entity(result)

        return None

    @staticmethod
    def student_user_exists(id_user: int | str) -> bool:
        """Verifica si el usuario autenticado tiene registro de estudiante."""
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT 1
                FROM students
                WHERE id_user = %s
                LIMIT 1;
            """
            cursor.execute(query, (id_user,))
            return cursor.fetchone() is not None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def course_exists_with_cursor(cursor, code_course: int | str) -> bool:
        """Verifica si un curso existe usando un cursor transaccional."""
        query = """
            SELECT 1
            FROM courses
            WHERE code_course = %s
            LIMIT 1;
        """
        cursor.execute(query, (code_course,))
        return cursor.fetchone() is not None

    @staticmethod
    def student_has_paid_enrollment(
        cursor,
        id_user: int | str,
        code_course: int | str,
    ) -> bool:
        """Verifica si el estudiante ya tiene inscripción confirmada en el curso."""
        query = """
            SELECT 1
            FROM enrollments e
            INNER JOIN students s ON e.id_student = s.id_student
            INNER JOIN receipts r ON r.id_enrollment = e.id_enrollment
            WHERE s.id_user = %s
              AND e.code_course = %s
              AND r.status = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_user, code_course, ReceiptStatus.PAID.value))
        return cursor.fetchone() is not None

    @staticmethod
    def student_has_pending_enrollment(
        cursor,
        id_user: int | str,
        code_course: int | str,
    ) -> bool:
        """Verifica si el estudiante tiene inscripción pendiente de pago."""
        query = """
            SELECT 1
            FROM enrollments e
            INNER JOIN students s ON e.id_student = s.id_student
            INNER JOIN receipts r ON r.id_enrollment = e.id_enrollment
            WHERE s.id_user = %s
              AND e.code_course = %s
              AND r.status = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_user, code_course, ReceiptStatus.PENDING.value))
        return cursor.fetchone() is not None

    @staticmethod
    def get_course_enrollment_status(
        cursor,
        id_user: int | str,
        code_course: int | str,
        reference_date: date | None = None,
    ) -> str:
        """
        Obtiene el estado de inscripción de un usuario estudiante en un curso.

        Estados retornados:
        - NO_INSCRITO
        - PENDIENTE_DE_PAGO
        - INSCRITO
        - VENCIDO
        """
        query = """
            SELECT r.status, r.due_date
            FROM enrollments e
            INNER JOIN students s ON e.id_student = s.id_student
            LEFT JOIN receipts r ON r.id_enrollment = e.id_enrollment
            WHERE s.id_user = %s
              AND e.code_course = %s
            ORDER BY e.id_enrollment DESC, r.id_receipt DESC
            LIMIT 1;
        """
        cursor.execute(query, (id_user, code_course))
        result = cursor.fetchone()

        if result is None:
            return EnrollmentModel.STATUS_NOT_ENROLLED

        receipt_status, due_date = result

        if receipt_status == ReceiptStatus.PAID.value:
            return EnrollmentModel.STATUS_ENROLLED

        if receipt_status == ReceiptStatus.PENDING.value:
            current_date = reference_date or date.today()
            if due_date and current_date > due_date:
                return EnrollmentModel.STATUS_EXPIRED
            return EnrollmentModel.STATUS_PENDING_PAYMENT

        if receipt_status == ReceiptStatus.EXPIRED.value:
            return EnrollmentModel.STATUS_EXPIRED

        return EnrollmentModel.STATUS_NOT_ENROLLED

    @staticmethod
    def _base_enrollment_select_from(confirmed_only: bool = False) -> str:
        """
        Fragmento base de la consulta de matrículas.

        Si confirmed_only es True, solo trae matrículas con recibo pagado. Esto
        mantiene la HU-19 alineada con la regla de HU-21: una inscripción solo
        queda confirmada después del pago.
        """
        confirmed_join = ""
        if confirmed_only:
            confirmed_join = f"""
            INNER JOIN receipts confirmed_receipt
                ON confirmed_receipt.id_enrollment = e.id_enrollment
               AND confirmed_receipt.status = '{ReceiptStatus.PAID.value}'
            """

        return f"""
            SELECT
                e.id_enrollment,
                s.id_student,
                student_user.id_user,
                student_user.name,
                student_user.password,
                student_user.role,
                student_user.email,
                student_user.birth_date,
                student_user.nationality,
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
                professor_user.id_user,
                professor_user.name,
                professor_user.password,
                professor_user.role,
                professor_user.email,
                professor_user.birth_date,
                professor_user.nationality,
                COUNT(confirmed_course_receipts.id_receipt) AS enrolled_students
            FROM enrollments e
            INNER JOIN students s ON e.id_student = s.id_student
            INNER JOIN users student_user ON s.id_user = student_user.id_user
            INNER JOIN courses c ON e.code_course = c.code_course
            INNER JOIN professors p ON c.id_professor = p.id_professor
            INNER JOIN users professor_user ON p.id_user = professor_user.id_user
            {confirmed_join}
            LEFT JOIN enrollments course_enrollments
                ON course_enrollments.code_course = c.code_course
            LEFT JOIN receipts confirmed_course_receipts
                ON confirmed_course_receipts.id_enrollment = course_enrollments.id_enrollment
               AND confirmed_course_receipts.status = '{ReceiptStatus.PAID.value}'
        """

    @staticmethod
    def _base_enrollment_group_by() -> str:
        return """
            GROUP BY
                e.id_enrollment,
                s.id_student,
                student_user.id_user,
                student_user.name,
                student_user.password,
                student_user.role,
                student_user.email,
                student_user.birth_date,
                student_user.nationality,
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
                professor_user.id_user,
                professor_user.name,
                professor_user.password,
                professor_user.role,
                professor_user.email,
                professor_user.birth_date,
                professor_user.nationality
        """

    @staticmethod
    def _map_enrollment_to_entity(row: tuple) -> Enrollment:
        (
            id_enrollment,
            id_student,
            student_id_user,
            student_name,
            student_password,
            student_role,
            student_email,
            student_birth_date,
            student_nationality,
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
            professor_id_user,
            professor_name,
            professor_password,
            professor_role,
            professor_email,
            professor_birth_date,
            professor_nationality,
            enrolled_students,
        ) = row

        student_user = User(
            id_user=student_id_user,
            name=student_name,
            password=student_password,
            role=UserRole(student_role),
            email=student_email,
            birth_date=student_birth_date,
            nationality=student_nationality,
        )

        student = Student(
            id_student=id_student,
            user=student_user,
        )

        professor_user = User(
            id_user=professor_id_user,
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

        return Enrollment(
            id_enrollment=id_enrollment,
            student=student,
            course=course,
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
