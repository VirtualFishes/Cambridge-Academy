from datetime import date

from ca_program.entities.fixed_values import PaymentMethod
from ca_program.entities.payment import Payment
from ca_program.models.receipt_model import ReceiptModel
from database.connection import get_connection


class PaymentModel:
    """Modelo de datos para pagos de recibos.

    Mantiene las consultas necesarias para:
    - HU-21: registrar pagos simulados de inscripciones.
    - HU-22: consultar historial de pagos de un estudiante.
    - HU-16: consultar todos los pagos realizados por estudiantes desde administración.
    """

    @staticmethod
    def create_payment(
        cursor,
        id_receipt: int,
        payment_method: PaymentMethod | str,
        payment_date: date,
    ) -> Payment:
        """
        Crea un pago usando el cursor de una transacción externa.

        Este método no hace commit ni rollback. El pago debe confirmarse desde
        la capa de servicios junto con el cambio de estado del recibo.
        """
        method = PaymentModel._normalize_payment_method(payment_method)

        query = """
            INSERT INTO payments (payment_date, payment_method, id_receipt)
            VALUES (%s, %s, %s)
            RETURNING id_payment;
        """
        cursor.execute(query, (payment_date, method.value, id_receipt))
        id_payment = cursor.fetchone()[0]

        return PaymentModel.get_payment_by_id(cursor, id_payment)

    @staticmethod
    def get_payment_by_id(cursor, id_payment: int) -> Payment | None:
        """
        Consulta un pago por su identificador usando un cursor existente.
        """
        query = f"""
            {PaymentModel._base_payment_select_from()}
            WHERE pay.id_payment = %s
            {PaymentModel._base_payment_group_by()}
            LIMIT 1;
        """
        cursor.execute(query, (id_payment,))
        result = cursor.fetchone()

        if result:
            return PaymentModel._map_payment_to_entity(result)

        return None

    @staticmethod
    def get_payment_by_receipt_id(id_receipt: int) -> Payment | None:
        """
        Consulta el pago asociado a un recibo.

        Según el diagrama, la relación Payment-Receipt es 1:1. Por eso este
        método retorna un solo pago.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {PaymentModel._base_payment_select_from()}
                WHERE pay.id_receipt = %s
                {PaymentModel._base_payment_group_by()}
                ORDER BY pay.id_payment DESC
                LIMIT 1;
            """
            cursor.execute(query, (id_receipt,))
            result = cursor.fetchone()

            if result:
                return PaymentModel._map_payment_to_entity(result)

            return None

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_payments_by_student_user_id(id_user: int | str) -> list[Payment]:
        """
        Consulta los pagos realizados por un usuario estudiante.

        HU-22: permite que un estudiante consulte su historial de pagos.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {PaymentModel._base_payment_select_from()}
                WHERE student_user.id_user = %s
                {PaymentModel._base_payment_group_by()}
                ORDER BY pay.payment_date DESC, pay.id_payment DESC;
            """
            cursor.execute(query, (id_user,))
            results = cursor.fetchall()

            return [PaymentModel._map_payment_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_all_payments() -> list[Payment]:
        """
        Consulta todos los pagos registrados en el sistema.

        HU-16: permite que el usuario administrativo consulte los pagos
        realizados por los estudiantes para control financiero.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                {PaymentModel._base_payment_select_from()}
                {PaymentModel._base_payment_group_by()}
                ORDER BY pay.payment_date DESC, pay.id_payment DESC;
            """
            cursor.execute(query)
            results = cursor.fetchall()

            return [PaymentModel._map_payment_to_entity(row) for row in results]

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_admin_payment_summary() -> dict:
        """
        Retorna un resumen financiero general para la vista administrativa.

        No reemplaza get_all_payments(); solo entrega métricas rápidas para
        tarjetas de resumen en la GUI administrativa.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT
                    COALESCE(SUM(r.amount), 0) AS total_paid,
                    COUNT(pay.id_payment) AS payment_count,
                    MAX(pay.payment_date) AS last_payment_date,
                    COUNT(*) FILTER (WHERE pay.payment_method = %s) AS cash_count,
                    COUNT(*) FILTER (WHERE pay.payment_method = %s) AS bank_count,
                    COUNT(*) FILTER (WHERE pay.payment_method = %s) AS card_count
                FROM payments pay
                INNER JOIN receipts r ON pay.id_receipt = r.id_receipt;
            """
            cursor.execute(
                query,
                (
                    PaymentMethod.CASH.value,
                    PaymentMethod.BANK.value,
                    PaymentMethod.CARD.value,
                ),
            )
            result = cursor.fetchone()

            if not result:
                return PaymentModel._empty_admin_summary()

            (
                total_paid,
                payment_count,
                last_payment_date,
                cash_count,
                bank_count,
                card_count,
            ) = result

            return {
                "total_paid": float(total_paid or 0),
                "payment_count": int(payment_count or 0),
                "last_payment_date": last_payment_date,
                "methods": {
                    PaymentMethod.CASH.value: int(cash_count or 0),
                    PaymentMethod.BANK.value: int(bank_count or 0),
                    PaymentMethod.CARD.value: int(card_count or 0),
                },
            }

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def payment_exists_for_receipt(cursor, id_receipt: int) -> bool:
        """
        Verifica si un recibo ya tiene un pago registrado.
        """
        query = """
            SELECT 1
            FROM payments
            WHERE id_receipt = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_receipt,))
        return cursor.fetchone() is not None

    @staticmethod
    def _base_payment_select_from() -> str:
        """
        Fragmento base para consultar pagos con su recibo completo.
        """
        return """
            SELECT
                pay.id_payment,
                pay.payment_date,
                pay.payment_method,
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
            FROM payments pay
            INNER JOIN receipts r ON pay.id_receipt = r.id_receipt
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
    def _base_payment_group_by() -> str:
        """
        GROUP BY completo para las consultas que usan _base_payment_select_from().
        """
        return """
            GROUP BY
                pay.id_payment,
                pay.payment_date,
                pay.payment_method,
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
    def _map_payment_to_entity(row: tuple) -> Payment:
        id_payment = row[0]
        payment_date = row[1]
        payment_method = row[2]
        receipt_data = row[3:]

        receipt = ReceiptModel._map_receipt_to_entity(receipt_data)

        return Payment(
            id_payment=id_payment,
            payment_date=payment_date,
            payment_method=PaymentMethod(payment_method),
            receipt=receipt,
        )

    @staticmethod
    def _normalize_payment_method(payment_method: PaymentMethod | str) -> PaymentMethod:
        if isinstance(payment_method, PaymentMethod):
            return payment_method

        return PaymentMethod(payment_method)

    @staticmethod
    def _empty_admin_summary() -> dict:
        return {
            "total_paid": 0.0,
            "payment_count": 0,
            "last_payment_date": None,
            "methods": {
                PaymentMethod.CASH.value: 0,
                PaymentMethod.BANK.value: 0,
                PaymentMethod.CARD.value: 0,
            },
        }
