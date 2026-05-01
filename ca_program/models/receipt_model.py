from datetime import date

from ca_program.entities.course import Course
from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import ReceiptStatus, UserRole
from ca_program.entities.professor import Professor
from ca_program.entities.receipt import Receipt
from ca_program.entities.student import Student
from ca_program.entities.user import User
from database.connection import get_connection


class ReceiptModel:
    """Modelo de datos para los recibos asociados a matrículas."""

    @staticmethod
    def create_pending_receipt(
        cursor,
        id_enrollment: int,
        amount: float,
        issue_date: date,
        due_date: date,
    ) -> Receipt:
        """
        Crea un recibo pendiente usando el cursor de una transacción externa.

        Este método no hace commit ni rollback. Esa responsabilidad queda en la
        capa de servicios, porque la creación del recibo forma parte del flujo
        completo de inscripción.
        """
        query = """
            INSERT INTO receipts (issue_date, due_date, id_enrollment, amount, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_receipt;
        """
        cursor.execute(
            query,
            (
                issue_date,
                due_date,
                id_enrollment,
                amount,
                ReceiptStatus.PENDING.value,
            ),
        )
        id_receipt = cursor.fetchone()[0]
        return ReceiptModel.get_receipt_by_id(cursor, id_receipt)

    @staticmethod
    def get_receipt_by_id(cursor, id_receipt: int) -> Receipt | None:
        """
        Consulta un recibo por su identificador usando un cursor existente.
        """
        query = f"""
            {ReceiptModel._base_receipt_select_from()}
            WHERE r.id_receipt = %s
            {ReceiptModel._base_receipt_group_by()}
            LIMIT 1;
        """
        cursor.execute(query, (id_receipt,))
        result = cursor.fetchone()

        if result:
            return ReceiptModel._map_receipt_to_entity(result)

        return None

    @staticmethod
    def get_receipt_by_enrollment_id(id_enrollment: int) -> Receipt | None:
        """
        Consulta el recibo asociado a una matrícula.

        Según el diagrama, la relación Receipt-Enrollment es 1:1. Por eso este
        método retorna un solo recibo.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {ReceiptModel._base_receipt_select_from()}
                WHERE r.id_enrollment = %s
                {ReceiptModel._base_receipt_group_by()}
                ORDER BY r.id_receipt DESC
                LIMIT 1;
            """
            cursor.execute(query, (id_enrollment,))
            result = cursor.fetchone()

            if result:
                return ReceiptModel._map_receipt_to_entity(result)

            return None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_receipt_by_student_and_course(
        cursor,
        id_user: int | str,
        code_course: int | str,
    ) -> Receipt | None:
        """
        Consulta el recibo de un usuario estudiante para un curso específico.
        """
        query = f"""
            {ReceiptModel._base_receipt_select_from()}
            WHERE student_user.id_user = %s
              AND c.code_course = %s
            {ReceiptModel._base_receipt_group_by()}
            ORDER BY r.id_receipt DESC
            LIMIT 1;
        """
        cursor.execute(query, (id_user, code_course))
        result = cursor.fetchone()

        if result:
            return ReceiptModel._map_receipt_to_entity(result)

        return None

    @staticmethod
    def get_pending_receipt_by_student_and_course(
        cursor,
        id_user: int | str,
        code_course: int | str,
    ) -> Receipt | None:
        """
        Consulta el recibo pendiente de un estudiante para un curso.
        """
        return ReceiptModel._get_receipt_by_student_course_and_status(
            cursor=cursor,
            id_user=id_user,
            code_course=code_course,
            status=ReceiptStatus.PENDING,
        )

    @staticmethod
    def get_paid_receipt_by_student_and_course(
        cursor,
        id_user: int | str,
        code_course: int | str,
    ) -> Receipt | None:
        """
        Consulta el recibo pagado de un estudiante para un curso.
        """
        return ReceiptModel._get_receipt_by_student_course_and_status(
            cursor=cursor,
            id_user=id_user,
            code_course=code_course,
            status=ReceiptStatus.PAID,
        )

    @staticmethod
    def get_receipts_by_student_user_id(id_user: int | str) -> list[Receipt]:
        """
        Consulta los recibos de un usuario estudiante.

        Este método queda preparado para HU-22: consultar historial de pagos.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {ReceiptModel._base_receipt_select_from()}
                WHERE student_user.id_user = %s
                {ReceiptModel._base_receipt_group_by()}
                ORDER BY r.issue_date DESC, r.id_receipt DESC;
            """
            cursor.execute(query, (id_user,))
            results = cursor.fetchall()

            return [ReceiptModel._map_receipt_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def mark_receipt_as_paid(cursor, id_receipt: int) -> Receipt | None:
        """
        Marca un recibo como pagado dentro de una transacción externa.
        """
        query = """
            UPDATE receipts
            SET status = %s
            WHERE id_receipt = %s
            RETURNING id_receipt;
        """
        cursor.execute(query, (ReceiptStatus.PAID.value, id_receipt))
        result = cursor.fetchone()

        if not result:
            return None

        return ReceiptModel.get_receipt_by_id(cursor, result[0])

    @staticmethod
    def mark_receipt_as_expired(cursor, id_receipt: int) -> Receipt | None:
        """
        Marca un recibo como vencido dentro de una transacción externa.
        """
        query = """
            UPDATE receipts
            SET status = %s
            WHERE id_receipt = %s
            RETURNING id_receipt;
        """
        cursor.execute(query, (ReceiptStatus.EXPIRED.value, id_receipt))
        result = cursor.fetchone()

        if not result:
            return None

        return ReceiptModel.get_receipt_by_id(cursor, result[0])

    @staticmethod
    def delete_receipt_by_id(cursor, id_receipt: int) -> bool:
        """
        Elimina permanentemente un recibo usando un cursor transaccional.

        Se usará cuando una inscripción pendiente venza y el estudiante quiera
        intentar inscribirse nuevamente en el mismo curso.
        """
        query = """
            DELETE FROM receipts
            WHERE id_receipt = %s;
        """
        cursor.execute(query, (id_receipt,))
        return cursor.rowcount > 0

    @staticmethod
    def is_receipt_expired(receipt: Receipt, reference_date: date | None = None) -> bool:
        """
        Verifica si un recibo pendiente ya superó su fecha límite de pago.
        """
        if not receipt or receipt.status != ReceiptStatus.PENDING:
            return False

        current_date = reference_date or date.today()
        return current_date > receipt.due_date

    @staticmethod
    def _get_receipt_by_student_course_and_status(
        cursor,
        id_user: int | str,
        code_course: int | str,
        status: ReceiptStatus,
    ) -> Receipt | None:
        query = f"""
            {ReceiptModel._base_receipt_select_from()}
            WHERE student_user.id_user = %s
              AND c.code_course = %s
              AND r.status = %s
            {ReceiptModel._base_receipt_group_by()}
            ORDER BY r.id_receipt DESC
            LIMIT 1;
        """
        cursor.execute(query, (id_user, code_course, status.value))
        result = cursor.fetchone()

        if result:
            return ReceiptModel._map_receipt_to_entity(result)

        return None

    @staticmethod
    def _base_receipt_select_from() -> str:
        """
        Fragmento base para consultar recibos con su inscripción completa.
        """
        return """
            SELECT
                r.id_receipt,
                r.issue_date,
                r.due_date,
                r.amount,
                r.status,
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
                COUNT(course_enrollments.id_enrollment) AS enrolled_students
            FROM receipts r
            INNER JOIN enrollments e ON r.id_enrollment = e.id_enrollment
            INNER JOIN students s ON e.id_student = s.id_student
            INNER JOIN users student_user ON s.id_user = student_user.id_user
            INNER JOIN courses c ON e.code_course = c.code_course
            INNER JOIN professors p ON c.id_professor = p.id_professor
            INNER JOIN users professor_user ON p.id_user = professor_user.id_user
            LEFT JOIN enrollments course_enrollments
                ON course_enrollments.code_course = c.code_course
        """

    @staticmethod
    def _base_receipt_group_by() -> str:
        return """
            GROUP BY
                r.id_receipt,
                r.issue_date,
                r.due_date,
                r.amount,
                r.status,
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
    def _map_receipt_to_entity(row: tuple) -> Receipt:
        (
            id_receipt,
            issue_date,
            due_date,
            amount,
            receipt_status,
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

        enrollment = Enrollment(
            id_enrollment=id_enrollment,
            student=student,
            course=course,
        )

        return Receipt(
            id_receipt=id_receipt,
            issue_date=issue_date,
            due_date=due_date,
            amount=float(amount),
            status=ReceiptStatus(receipt_status),
            enrollment=enrollment,
        )
