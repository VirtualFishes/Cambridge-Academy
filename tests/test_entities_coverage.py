from datetime import date, timedelta

import pytest

from ca_program.entities._validators import (
    require_date,
    require_date_order,
    require_enum_member,
    require_instance,
    require_non_empty_string,
    require_number_in_range,
    require_positive_integer,
    require_positive_number,
)
from ca_program.entities.course import Course
from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import AcademicStatus, PaymentMethod, ReceiptStatus, UserRole
from ca_program.entities.grade import Grade
from ca_program.entities.payment import Payment
from ca_program.entities.professor import Professor
from ca_program.entities.receipt import Receipt
from ca_program.entities.student import Student
from ca_program.entities.user import User


TODAY = date(2026, 5, 1)


def make_user(role=UserRole.STUDENT, id_user=1, email="persona@correo.com"):
    return User(
        id_user=id_user,
        name="Usuario Prueba",
        password="clave123",
        role=role,
        email=email,
        birth_date=date(2000, 1, 1),
        nationality="Colombiana",
    )


def make_student():
    return Student(id_student="100200300", user=make_user(UserRole.STUDENT, 10, "estudiante@correo.com"))


def make_professor():
    return Professor(
        id_professor="900800700",
        professional_title="Licenciado en idiomas",
        user=make_user(UserRole.PROFESSOR, 20, "profesor@correo.com"),
    )


def make_course():
    return Course(
        code_course="ENG-101",
        name="Inglés básico",
        description="Curso inicial de inglés",
        price=450000.0,
        duration_days=60,
        intensity_hours=80,
        schedule="Lunes y miércoles 18:00",
        location="Sede principal",
        start_date=TODAY,
        end_date=TODAY + timedelta(days=60),
        professor=make_professor(),
    )


def make_enrollment():
    return Enrollment(id_enrollment=1, student=make_student(), course=make_course())


def make_receipt():
    return Receipt(
        id_receipt=1,
        issue_date=TODAY,
        due_date=TODAY + timedelta(days=10),
        amount=450000.0,
        status=ReceiptStatus.PENDING,
        enrollment=make_enrollment(),
    )


class TestValidators:
    def test_require_instance_accepts_expected_type(self):
        require_instance("abc", str, "campo")

    def test_require_instance_rejects_wrong_type(self):
        with pytest.raises(TypeError):
            require_instance(123, str, "campo")

    def test_require_enum_member_accepts_enum(self):
        require_enum_member(UserRole.ADMIN, UserRole, "role")

    def test_require_enum_member_rejects_non_enum(self):
        with pytest.raises(TypeError):
            require_enum_member("admin", UserRole, "role")

    def test_require_non_empty_string_accepts_text(self):
        require_non_empty_string(" texto ", "nombre")

    @pytest.mark.parametrize("value,expected", [(123, TypeError), ("   ", ValueError)])
    def test_require_non_empty_string_rejects_invalid_values(self, value, expected):
        with pytest.raises(expected):
            require_non_empty_string(value, "nombre")

    def test_require_positive_integer_accepts_positive_int(self):
        require_positive_integer(1, "id")

    @pytest.mark.parametrize("value,expected", [(True, TypeError), (1.5, TypeError), (0, ValueError), (-3, ValueError)])
    def test_require_positive_integer_rejects_invalid_values(self, value, expected):
        with pytest.raises(expected):
            require_positive_integer(value, "id")

    def test_require_positive_number_accepts_positive_number(self):
        require_positive_number(10.5, "precio")

    @pytest.mark.parametrize("value,expected", [(False, TypeError), ("10", TypeError), (0, ValueError), (-1, ValueError)])
    def test_require_positive_number_rejects_invalid_values(self, value, expected):
        with pytest.raises(expected):
            require_positive_number(value, "precio")

    def test_require_number_in_range_accepts_limits(self):
        require_number_in_range(0.0, "nota", 0.0, 5.0)
        require_number_in_range(5.0, "nota", 0.0, 5.0)

    @pytest.mark.parametrize("value,expected", [(True, TypeError), ("3", TypeError), (-0.1, ValueError), (5.1, ValueError)])
    def test_require_number_in_range_rejects_invalid_values(self, value, expected):
        with pytest.raises(expected):
            require_number_in_range(value, "nota", 0.0, 5.0)

    def test_require_date_accepts_date(self):
        require_date(TODAY, "fecha")

    def test_require_date_rejects_non_date(self):
        with pytest.raises(TypeError):
            require_date("2026-05-01", "fecha")

    def test_require_date_order_accepts_valid_order(self):
        require_date_order(TODAY, TODAY + timedelta(days=1), "inicio", "fin")

    def test_require_date_order_rejects_invalid_order(self):
        with pytest.raises(ValueError):
            require_date_order(TODAY, TODAY - timedelta(days=1), "inicio", "fin")


class TestDomainEntities:
    def test_user_valid_creation_and_string(self):
        user = make_user()
        assert user.name == "Usuario Prueba"
        assert str(user) == "Usuario Prueba"

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"id_user": 0}, ValueError),
            ({"name": ""}, ValueError),
            ({"password": ""}, ValueError),
            ({"role": "student"}, TypeError),
            ({"email": "correo_sin_arroba"}, ValueError),
            ({"email": "@correo.com"}, ValueError),
            ({"email": "persona@"}, ValueError),
            ({"birth_date": "2000-01-01"}, TypeError),
            ({"nationality": ""}, ValueError),
        ],
    )
    def test_user_rejects_invalid_data(self, kwargs, expected):
        data = dict(
            id_user=1,
            name="Usuario Prueba",
            password="clave123",
            role=UserRole.STUDENT,
            email="persona@correo.com",
            birth_date=date(2000, 1, 1),
            nationality="Colombiana",
        )
        data.update(kwargs)
        with pytest.raises(expected):
            User(**data)

    def test_student_valid_creation_and_string(self):
        student = make_student()
        assert student.id_student == "100200300"
        assert str(student) == student.user.name

    def test_student_requires_student_role(self):
        with pytest.raises(ValueError):
            Student(id_student="100200300", user=make_user(UserRole.ADMIN))

    def test_student_rejects_empty_id_and_wrong_user_type(self):
        with pytest.raises(ValueError):
            Student(id_student="", user=make_user(UserRole.STUDENT))
        with pytest.raises(TypeError):
            Student(id_student="100200300", user="no-user")

    def test_professor_valid_creation_and_string(self):
        professor = make_professor()
        assert professor.professional_title == "Licenciado en idiomas"
        assert str(professor) == professor.user.name

    def test_professor_requires_professor_role(self):
        with pytest.raises(ValueError):
            Professor(id_professor="900800700", professional_title="Docente", user=make_user(UserRole.STUDENT))

    def test_professor_rejects_invalid_fields(self):
        with pytest.raises(ValueError):
            Professor(id_professor="", professional_title="Docente", user=make_user(UserRole.PROFESSOR))
        with pytest.raises(ValueError):
            Professor(id_professor="900800700", professional_title="", user=make_user(UserRole.PROFESSOR))
        with pytest.raises(TypeError):
            Professor(id_professor="900800700", professional_title="Docente", user=None)

    def test_course_valid_creation_normalizes_code_and_string(self):
        course = Course(
            code_course=101,
            name="Inglés básico",
            description="Curso inicial de inglés",
            price=450000.0,
            duration_days=60,
            intensity_hours=80,
            schedule="Lunes y miércoles 18:00",
            location="Sede principal",
            start_date=TODAY,
            end_date=TODAY + timedelta(days=60),
            professor=make_professor(),
        )
        assert course.code_course == "101"
        assert str(course) == "Inglés básico"

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"code_course": None}, ValueError),
            ({"name": ""}, ValueError),
            ({"description": ""}, ValueError),
            ({"price": 0}, ValueError),
            ({"duration_days": 0}, ValueError),
            ({"intensity_hours": 0}, ValueError),
            ({"schedule": ""}, ValueError),
            ({"location": ""}, ValueError),
            ({"start_date": TODAY + timedelta(days=2), "end_date": TODAY}, ValueError),
            ({"professor": "no-professor"}, TypeError),
        ],
    )
    def test_course_rejects_invalid_data(self, kwargs, expected):
        data = dict(
            code_course="ENG-101",
            name="Inglés básico",
            description="Curso inicial de inglés",
            price=450000.0,
            duration_days=60,
            intensity_hours=80,
            schedule="Lunes y miércoles 18:00",
            location="Sede principal",
            start_date=TODAY,
            end_date=TODAY + timedelta(days=60),
            professor=make_professor(),
        )
        data.update(kwargs)
        with pytest.raises(expected):
            Course(**data)

    def test_enrollment_valid_creation_and_string(self):
        enrollment = make_enrollment()
        assert enrollment.id_enrollment == 1
        assert str(enrollment) == f"{enrollment.student.user.name} - {enrollment.course.name}"

    def test_enrollment_rejects_invalid_data(self):
        with pytest.raises(ValueError):
            Enrollment(id_enrollment=0, student=make_student(), course=make_course())
        with pytest.raises(TypeError):
            Enrollment(id_enrollment=1, student="no-student", course=make_course())
        with pytest.raises(TypeError):
            Enrollment(id_enrollment=1, student=make_student(), course="no-course")

    def test_grade_valid_creation_and_string(self):
        grade = Grade(
            id_grade=1,
            enrollment=make_enrollment(),
            grade1=4.0,
            grade2=4.5,
            grade3=5.0,
            average=4.5,
            status=AcademicStatus.PASSED,
        )
        assert grade.average == 4.5
        assert "Nota 1" in str(grade)

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"id_grade": 0}, ValueError),
            ({"enrollment": None}, TypeError),
            ({"grade1": -1}, ValueError),
            ({"grade2": 5.5}, ValueError),
            ({"grade3": True}, TypeError),
            ({"average": 8}, ValueError),
            ({"status": "passed"}, TypeError),
        ],
    )
    def test_grade_rejects_invalid_data(self, kwargs, expected):
        data = dict(
            id_grade=1,
            enrollment=make_enrollment(),
            grade1=4.0,
            grade2=4.5,
            grade3=5.0,
            average=4.5,
            status=AcademicStatus.PASSED,
        )
        data.update(kwargs)
        with pytest.raises(expected):
            Grade(**data)

    def test_receipt_valid_creation_and_string(self):
        receipt = make_receipt()
        assert receipt.status is ReceiptStatus.PENDING
        assert str(receipt) == "Recibo 1 - pending"

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"id_receipt": 0}, ValueError),
            ({"due_date": TODAY - timedelta(days=1)}, ValueError),
            ({"amount": 0}, ValueError),
            ({"status": "pending"}, TypeError),
            ({"enrollment": "no-enrollment"}, TypeError),
        ],
    )
    def test_receipt_rejects_invalid_data(self, kwargs, expected):
        data = dict(
            id_receipt=1,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=10),
            amount=450000.0,
            status=ReceiptStatus.PENDING,
            enrollment=make_enrollment(),
        )
        data.update(kwargs)
        with pytest.raises(expected):
            Receipt(**data)

    def test_payment_valid_creation_and_string(self):
        payment = Payment(
            id_payment=1,
            payment_date=TODAY,
            payment_method=PaymentMethod.CARD,
            receipt=make_receipt(),
        )
        assert payment.payment_method is PaymentMethod.CARD
        assert str(payment) == "Pago 1 - card"

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"id_payment": 0}, ValueError),
            ({"payment_date": "2026-05-01"}, TypeError),
            ({"payment_method": "card"}, TypeError),
            ({"receipt": None}, TypeError),
        ],
    )
    def test_payment_rejects_invalid_data(self, kwargs, expected):
        data = dict(
            id_payment=1,
            payment_date=TODAY,
            payment_method=PaymentMethod.CARD,
            receipt=make_receipt(),
        )
        data.update(kwargs)
        with pytest.raises(expected):
            Payment(**data)
