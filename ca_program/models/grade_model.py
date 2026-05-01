from ca_program.entities.fixed_values import AcademicStatus, ReceiptStatus
from ca_program.entities.grade import Grade
from ca_program.models.enrollment_model import EnrollmentModel
from database.connection import get_connection


class GradeModel:
    """Modelo de datos para el registro académico de notas."""

    @staticmethod
    def create_grade(
        cursor,
        id_enrollment: int,
        grade1: float,
        grade2: float,
        grade3: float,
        average: float,
        status: AcademicStatus | str,
    ) -> Grade:
        """
        Crea un registro de notas usando un cursor transaccional externo.

        No realiza commit ni rollback. La capa de servicio debe controlar la
        transacción completa para validar profesor, curso, matrícula y notas
        antes de confirmar los cambios.
        """
        status_value = GradeModel._status_to_value(status)

        query = """
            INSERT INTO grades (
                id_enrollment,
                grade1,
                grade2,
                grade3,
                avarage,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_grade;
        """
        cursor.execute(
            query,
            (
                id_enrollment,
                grade1,
                grade2,
                grade3,
                average,
                status_value,
            ),
        )
        id_grade = cursor.fetchone()[0]

        grade = GradeModel.get_grade_by_id(
            cursor=cursor,
            id_grade=id_grade,
        )

        if grade is None:
            raise ValueError("No fue posible recuperar las notas registradas.")

        return grade

    @staticmethod
    def update_grade(
        cursor,
        id_grade: int | str,
        grade1: float,
        grade2: float,
        grade3: float,
        average: float,
        status: AcademicStatus | str,
    ) -> Grade:
        """
        Actualiza un registro de notas usando un cursor transaccional externo.

        No realiza commit ni rollback. La capa de servicio debe validar antes
        que la nota pertenezca al curso asignado al profesor autenticado.
        """
        status_value = GradeModel._status_to_value(status)

        query = """
            UPDATE grades
            SET
                grade1 = %s,
                grade2 = %s,
                grade3 = %s,
                avarage = %s,
                status = %s
            WHERE id_grade = %s;
        """
        cursor.execute(
            query,
            (
                grade1,
                grade2,
                grade3,
                average,
                status_value,
                id_grade,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError("No fue posible actualizar las notas indicadas.")

        grade = GradeModel.get_grade_by_id(
            cursor=cursor,
            id_grade=id_grade,
        )

        if grade is None:
            raise ValueError("No fue posible recuperar las notas actualizadas.")

        return grade

    @staticmethod
    def get_grade_by_id(cursor, id_grade: int) -> Grade | None:
        """Consulta un registro de notas por identificador usando un cursor existente."""
        query = f"""
            {GradeModel._base_grade_select_from()}
            WHERE g.id_grade = %s
            {EnrollmentModel._base_enrollment_group_by()},
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status
            LIMIT 1;
        """
        cursor.execute(query, (id_grade,))
        result = cursor.fetchone()

        if result:
            return GradeModel._map_to_entity(result)

        return None

    @staticmethod
    def get_grade_by_enrollment_id(id_enrollment: int) -> Grade | None:
        """Consulta las notas asociadas a una matrícula."""
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return GradeModel.get_grade_by_enrollment_id_with_cursor(
                cursor=cursor,
                id_enrollment=id_enrollment,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_grade_by_enrollment_id_with_cursor(cursor, id_enrollment: int) -> Grade | None:
        """Consulta las notas asociadas a una matrícula usando un cursor externo."""
        query = f"""
            {GradeModel._base_grade_select_from()}
            WHERE e.id_enrollment = %s
            {EnrollmentModel._base_enrollment_group_by()},
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status
            ORDER BY g.id_grade DESC
            LIMIT 1;
        """
        cursor.execute(query, (id_enrollment,))
        result = cursor.fetchone()

        if result:
            return GradeModel._map_to_entity(result)

        return None

    @staticmethod
    def grade_exists_for_enrollment(cursor, id_enrollment: int) -> bool:
        """Verifica si una matrícula ya tiene notas registradas."""
        query = """
            SELECT 1
            FROM grades
            WHERE id_enrollment = %s
            LIMIT 1;
        """
        cursor.execute(query, (id_enrollment,))
        return cursor.fetchone() is not None

    @staticmethod
    def get_grades_by_course_and_professor_id(
        code_course: int | str,
        id_professor: int | str,
    ) -> list[Grade]:
        """
        Consulta las notas registradas de un curso asignado a un profesor.

        El filtro por profesor evita exponer notas de cursos que no pertenecen
        al docente autenticado.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return GradeModel.get_grades_by_course_and_professor_id_with_cursor(
                cursor=cursor,
                code_course=code_course,
                id_professor=id_professor,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_grades_by_course_and_professor_id_with_cursor(
        cursor,
        code_course: int | str,
        id_professor: int | str,
    ) -> list[Grade]:
        """
        Consulta las notas de un curso del profesor usando un cursor existente.

        Solo retorna notas asociadas a matrículas confirmadas con recibo pagado,
        manteniendo el mismo criterio usado para registrar notas.
        """
        query = f"""
            {GradeModel._base_grade_select_from()}
            WHERE c.code_course = %s
              AND c.id_professor = %s
              AND EXISTS (
                  SELECT 1
                  FROM receipts paid_receipt
                  WHERE paid_receipt.id_enrollment = e.id_enrollment
                    AND paid_receipt.status = %s
              )
            {EnrollmentModel._base_enrollment_group_by()},
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status
            ORDER BY student_user.name ASC, s.id_student ASC, g.id_grade DESC;
        """
        cursor.execute(query, (code_course, id_professor, ReceiptStatus.PAID.value))
        results = cursor.fetchall()

        return [GradeModel._map_to_entity(row) for row in results]

    @staticmethod
    def get_grade_by_id_course_and_professor_id(
        cursor,
        id_grade: int | str,
        code_course: int | str,
        id_professor: int | str,
    ) -> Grade | None:
        """
        Consulta una nota específica validando curso, profesor e inscripción.

        Este método es la barrera de seguridad para HU-28: antes de modificar
        notas, confirma que la calificación existe, pertenece al curso indicado,
        el curso está asignado al profesor autenticado y la matrícula está
        confirmada mediante recibo pagado.
        """
        query = f"""
            {GradeModel._base_grade_select_from()}
            WHERE g.id_grade = %s
              AND c.code_course = %s
              AND c.id_professor = %s
              AND EXISTS (
                  SELECT 1
                  FROM receipts paid_receipt
                  WHERE paid_receipt.id_enrollment = e.id_enrollment
                    AND paid_receipt.status = %s
              )
            {EnrollmentModel._base_enrollment_group_by()},
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status
            LIMIT 1;
        """
        cursor.execute(
            query,
            (
                id_grade,
                code_course,
                id_professor,
                ReceiptStatus.PAID.value,
            ),
        )
        result = cursor.fetchone()

        if result:
            return GradeModel._map_to_entity(result)

        return None


    @staticmethod
    def get_grade_records_by_student_id(id_student: int | str) -> list[dict]:
        """
        Consulta el registro académico de un estudiante.

        Retorna las matrículas confirmadas del estudiante junto con sus notas,
        cuando ya existen. Usa LEFT JOIN sobre grades para que los cursos
        pendientes de calificación también puedan mostrarse en la GUI del
        estudiante como "Pendiente".
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return GradeModel.get_grade_records_by_student_id_with_cursor(
                cursor=cursor,
                id_student=id_student,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_grade_records_by_student_id_with_cursor(
        cursor,
        id_student: int | str,
    ) -> list[dict]:
        """
        Consulta el registro académico de un estudiante usando cursor externo.

        Solo se consideran matrículas confirmadas con recibo pagado. El filtro
        por id_student permite que la capa de servicio muestre exclusivamente
        las notas del estudiante autenticado.
        """
        query = """
            SELECT
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status,
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
            INNER JOIN receipts confirmed_receipt
                ON confirmed_receipt.id_enrollment = e.id_enrollment
               AND confirmed_receipt.status = %s
            LEFT JOIN LATERAL (
                SELECT latest_grade.*
                FROM grades latest_grade
                WHERE latest_grade.id_enrollment = e.id_enrollment
                ORDER BY latest_grade.id_grade DESC
                LIMIT 1
            ) g ON TRUE
            LEFT JOIN enrollments course_enrollments
                ON course_enrollments.code_course = c.code_course
            LEFT JOIN receipts confirmed_course_receipts
                ON confirmed_course_receipts.id_enrollment = course_enrollments.id_enrollment
               AND confirmed_course_receipts.status = %s
            WHERE s.id_student = %s
            GROUP BY
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status,
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
            ORDER BY c.name ASC, e.id_enrollment ASC;
        """
        cursor.execute(
            query,
            (
                ReceiptStatus.PAID.value,
                ReceiptStatus.PAID.value,
                id_student,
            ),
        )
        results = cursor.fetchall()

        return [GradeModel._map_student_grade_record(row) for row in results]

    @staticmethod
    def get_grade_records_by_student_user_id(id_user: int | str) -> list[dict]:
        """
        Consulta el registro académico usando el id_user del estudiante.

        Este método mantiene el modelo disponible para servicios que ya
        trabajen directamente con el usuario autenticado.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = """
                SELECT id_student
                FROM students
                WHERE id_user = %s
                LIMIT 1;
            """
            cursor.execute(query, (id_user,))
            result = cursor.fetchone()

            if not result:
                return []

            return GradeModel.get_grade_records_by_student_id_with_cursor(
                cursor=cursor,
                id_student=result[0],
            )

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_grade_records_by_student_id_for_admin(id_student: int | str) -> list[dict]:
        """
        Consulta el registro académico de un estudiante para uso administrativo.

        HU-17 requiere que el personal administrativo seleccione un estudiante
        y vea su registro completo de notas. La consulta reutiliza el mismo
        criterio académico del estudiante: solo matrículas confirmadas con
        recibo pagado, incluyendo cursos pendientes de calificación mediante
        LEFT JOIN sobre grades.
        """
        connection = get_connection()
        cursor = connection.cursor()

        try:
            return GradeModel.get_grade_records_by_student_id_for_admin_with_cursor(
                cursor=cursor,
                id_student=id_student,
            )

        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_grade_records_by_student_id_for_admin_with_cursor(
        cursor,
        id_student: int | str,
    ) -> list[dict]:
        """
        Consulta el registro académico de un estudiante para administración.

        El modelo no decide permisos de usuario; esa responsabilidad queda en
        GradeService. Aquí solo se centraliza la consulta para que HU-17 no
        duplique SQL ni dependa de la GUI.
        """
        return GradeModel.get_grade_records_by_student_id_with_cursor(
            cursor=cursor,
            id_student=id_student,
        )

    get_grade_by_enrollment = get_grade_by_enrollment_id
    get_by_enrollment_id = get_grade_by_enrollment_id
    exists_for_enrollment = grade_exists_for_enrollment
    has_grade_for_enrollment = grade_exists_for_enrollment
    get_course_grades_by_professor = get_grades_by_course_and_professor_id
    get_grades_by_assigned_course = get_grades_by_course_and_professor_id
    get_grade_for_update = get_grade_by_id_course_and_professor_id
    get_editable_grade_by_context = get_grade_by_id_course_and_professor_id
    get_grade_by_context = get_grade_by_id_course_and_professor_id
    update_student_grade = update_grade
    modify_grade = update_grade
    get_student_grade_records = get_grade_records_by_student_id
    get_grade_record_by_student_id = get_grade_records_by_student_id
    get_student_academic_record = get_grade_records_by_student_id
    get_student_grade_records_by_user_id = get_grade_records_by_student_user_id
    get_grade_record_by_student_user_id = get_grade_records_by_student_user_id
    get_admin_student_grade_records = get_grade_records_by_student_id_for_admin
    get_student_grade_records_for_admin = get_grade_records_by_student_id_for_admin
    get_admin_grade_record_by_student_id = get_grade_records_by_student_id_for_admin
    get_student_academic_record_for_admin = get_grade_records_by_student_id_for_admin

    @staticmethod
    def _base_grade_select_from() -> str:
        return f"""
            SELECT
                g.id_grade,
                g.grade1,
                g.grade2,
                g.grade3,
                g.avarage,
                g.status,
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
            FROM grades g
            INNER JOIN enrollments e ON g.id_enrollment = e.id_enrollment
            INNER JOIN students s ON e.id_student = s.id_student
            INNER JOIN users student_user ON s.id_user = student_user.id_user
            INNER JOIN courses c ON e.code_course = c.code_course
            INNER JOIN professors p ON c.id_professor = p.id_professor
            INNER JOIN users professor_user ON p.id_user = professor_user.id_user
            LEFT JOIN enrollments course_enrollments
                ON course_enrollments.code_course = c.code_course
            LEFT JOIN receipts confirmed_course_receipts
                ON confirmed_course_receipts.id_enrollment = course_enrollments.id_enrollment
               AND confirmed_course_receipts.status = '{ReceiptStatus.PAID.value}'
        """

    @staticmethod
    def _map_to_entity(row: tuple) -> Grade:
        (
            id_grade,
            grade1,
            grade2,
            grade3,
            average,
            status,
            *enrollment_data,
        ) = row

        enrollment = EnrollmentModel._map_enrollment_to_entity(tuple(enrollment_data))

        return Grade(
            id_grade=id_grade,
            enrollment=enrollment,
            grade1=float(grade1),
            grade2=float(grade2),
            grade3=float(grade3),
            average=float(average),
            status=AcademicStatus(status),
        )


    @staticmethod
    def _map_student_grade_record(row: tuple) -> dict:
        """
        Mapea una fila de registro académico estudiantil.

        La nota puede ser None cuando el curso tiene inscripción confirmada,
        pero el profesor todavía no ha registrado calificaciones.
        """
        (
            id_grade,
            grade1,
            grade2,
            grade3,
            average,
            status,
            *enrollment_data,
        ) = row

        enrollment = EnrollmentModel._map_enrollment_to_entity(tuple(enrollment_data))
        grade = None

        if id_grade is not None:
            grade = Grade(
                id_grade=id_grade,
                enrollment=enrollment,
                grade1=float(grade1),
                grade2=float(grade2),
                grade3=float(grade3),
                average=float(average),
                status=AcademicStatus(status),
            )

        return {
            "enrollment": enrollment,
            "grade": grade,
            "has_grade": grade is not None,
        }

    @staticmethod
    def _status_to_value(status: AcademicStatus | str) -> str:
        if isinstance(status, AcademicStatus):
            return status.value

        return str(status).strip()
