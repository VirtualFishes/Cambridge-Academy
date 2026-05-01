from datetime import date

import pytest

from ca_program.entities.course import Course
from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import (
    AcademicStatus,
    PaymentMethod,
    ReceiptStatus,
    UserRole,
)
from ca_program.entities.grade import Grade
from ca_program.entities.payment import Payment
from ca_program.entities.professor import Professor
from ca_program.entities.receipt import Receipt
from ca_program.entities.student import Student
from ca_program.entities.user import User


# ---------------------------------------------------------------------
# Fábricas de objetos válidos
# ---------------------------------------------------------------------

def make_user(
    id_user=1,
    name="Carlos Pérez",
    password="1234",
    role=UserRole.STUDENT,
    email="carlos@example.com",
    birth_date=date(2000, 5, 10),
    nationality="Colombiana",
):
    return User(
        id_user=id_user,
        name=name,
        password=password,
        role=role,
        email=email,
        birth_date=birth_date,
        nationality=nationality,
    )


def make_student():
    user = make_user(role=UserRole.STUDENT)
    return Student(
        id_student="1001234567",
        user=user,
    )


def make_professor():
    user = make_user(
        id_user=2,
        name="Laura Gómez",
        role=UserRole.PROFESSOR,
        email="laura@example.com",
    )
    return Professor(
        id_professor="2001234567",
        professional_title="Licenciada en Inglés",
        user=user,
    )


def make_course():
    professor = make_professor()
    return Course(
        code_course="ENG-A1",
        name="Inglés A1",
        description="Curso básico de inglés",
        price=250000,
        duration_days=60,
        intensity_hours=80,
        schedule="Lunes y miércoles 6:00 PM",
        location="Sede principal",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 3, 10),
        professor=professor,
    )


def make_enrollment():
    return Enrollment(
        id_enrollment=1,
        student=make_student(),
        course=make_course(),
    )


def make_receipt():
    return Receipt(
        id_receipt=1,
        issue_date=date(2026, 1, 10),
        due_date=date(2026, 1, 20),
        amount=250000,
        status=ReceiptStatus.PENDING,
        enrollment=make_enrollment(),
    )


# ---------------------------------------------------------------------
# Pruebas de User
# ---------------------------------------------------------------------

def test_user_valido_se_crea_correctamente():
    user = make_user()

    assert user.id_user == 1
    assert user.name == "Carlos Pérez"
    assert user.role == UserRole.STUDENT
    assert str(user) == "Carlos Pérez"


@pytest.mark.parametrize(
    "email",
    [
        "",
        "correo_invalido",
        "@example.com",
        "usuario@",
    ],
)
def test_user_rechaza_correos_invalidos(email):
    with pytest.raises(ValueError):
        make_user(email=email)


def test_user_rechaza_id_no_positivo():
    with pytest.raises(ValueError):
        make_user(id_user=0)


def test_user_rechaza_rol_invalido():
    with pytest.raises(TypeError):
        make_user(role="student")


def test_user_rechaza_fecha_nacimiento_invalida():
    with pytest.raises(TypeError):
        make_user(birth_date="2000-05-10")


# ---------------------------------------------------------------------
# Pruebas de Student
# ---------------------------------------------------------------------

def test_student_valido_se_crea_correctamente():
    student = make_student()

    assert student.id_student == "1001234567"
    assert student.user.role == UserRole.STUDENT
    assert str(student) == student.user.name


def test_student_rechaza_usuario_con_rol_incorrecto():
    user = make_user(role=UserRole.PROFESSOR)

    with pytest.raises(ValueError):
        Student(
            id_student="1001234567",
            user=user,
        )


def test_student_rechaza_id_vacio():
    with pytest.raises(ValueError):
        Student(
            id_student="",
            user=make_user(role=UserRole.STUDENT),
        )


# ---------------------------------------------------------------------
# Pruebas de Professor
# ---------------------------------------------------------------------

def test_professor_valido_se_crea_correctamente():
    professor = make_professor()

    assert professor.id_professor == "2001234567"
    assert professor.professional_title == "Licenciada en Inglés"
    assert professor.user.role == UserRole.PROFESSOR
    assert str(professor) == professor.user.name


def test_professor_rechaza_usuario_con_rol_incorrecto():
    user = make_user(role=UserRole.STUDENT)

    with pytest.raises(ValueError):
        Professor(
            id_professor="2001234567",
            professional_title="Licenciado en Inglés",
            user=user,
        )


def test_professor_rechaza_titulo_profesional_vacio():
    with pytest.raises(ValueError):
        Professor(
            id_professor="2001234567",
            professional_title="",
            user=make_user(role=UserRole.PROFESSOR),
        )


# ---------------------------------------------------------------------
# Pruebas de Course
# ---------------------------------------------------------------------

def test_course_valido_se_crea_correctamente():
    course = make_course()

    assert course.code_course == "ENG-A1"
    assert course.name == "Inglés A1"
    assert course.price == 250000
    assert course.professor.user.role == UserRole.PROFESSOR
    assert str(course) == "Inglés A1"


def test_course_normaliza_codigo_numerico_a_texto():
    professor = make_professor()

    course = Course(
        code_course=101,
        name="Francés A1",
        description="Curso básico de francés",
        price=300000,
        duration_days=60,
        intensity_hours=80,
        schedule="Martes y jueves 6:00 PM",
        location="Sede principal",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 3, 10),
        professor=professor,
    )

    assert course.code_course == "101"


@pytest.mark.parametrize("price", [0, -100])
def test_course_rechaza_precio_no_positivo(price):
    professor = make_professor()

    with pytest.raises(ValueError):
        Course(
            code_course="ENG-A1",
            name="Inglés A1",
            description="Curso básico de inglés",
            price=price,
            duration_days=60,
            intensity_hours=80,
            schedule="Lunes y miércoles 6:00 PM",
            location="Sede principal",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 3, 10),
            professor=professor,
        )


def test_course_rechaza_fecha_final_anterior_a_fecha_inicial():
    professor = make_professor()

    with pytest.raises(ValueError):
        Course(
            code_course="ENG-A1",
            name="Inglés A1",
            description="Curso básico de inglés",
            price=250000,
            duration_days=60,
            intensity_hours=80,
            schedule="Lunes y miércoles 6:00 PM",
            location="Sede principal",
            start_date=date(2026, 3, 10),
            end_date=date(2026, 1, 10),
            professor=professor,
        )


def test_course_rechaza_profesor_invalido():
    with pytest.raises(TypeError):
        Course(
            code_course="ENG-A1",
            name="Inglés A1",
            description="Curso básico de inglés",
            price=250000,
            duration_days=60,
            intensity_hours=80,
            schedule="Lunes y miércoles 6:00 PM",
            location="Sede principal",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 3, 10),
            professor="profesor inválido",
        )


# ---------------------------------------------------------------------
# Pruebas de Enrollment
# ---------------------------------------------------------------------

def test_enrollment_valido_se_crea_correctamente():
    enrollment = make_enrollment()

    assert enrollment.id_enrollment == 1
    assert enrollment.student.user.role == UserRole.STUDENT
    assert enrollment.course.name == "Inglés A1"
    assert str(enrollment) == "Carlos Pérez - Inglés A1"


def test_enrollment_rechaza_id_no_positivo():
    with pytest.raises(ValueError):
        Enrollment(
            id_enrollment=0,
            student=make_student(),
            course=make_course(),
        )


def test_enrollment_rechaza_student_invalido():
    with pytest.raises(TypeError):
        Enrollment(
            id_enrollment=1,
            student="estudiante inválido",
            course=make_course(),
        )


def test_enrollment_rechaza_course_invalido():
    with pytest.raises(TypeError):
        Enrollment(
            id_enrollment=1,
            student=make_student(),
            course="curso inválido",
        )


# ---------------------------------------------------------------------
# Pruebas de Grade
# ---------------------------------------------------------------------

def test_grade_valida_se_crea_correctamente():
    grade = Grade(
        id_grade=1,
        enrollment=make_enrollment(),
        grade1=4.0,
        grade2=4.5,
        grade3=5.0,
        average=4.5,
        status=AcademicStatus.PASSED,
    )

    assert grade.id_grade == 1
    assert grade.average == 4.5
    assert grade.status == AcademicStatus.PASSED
    assert "Nota 1" in str(grade)


@pytest.mark.parametrize("grade_value", [-1, 5.1])
def test_grade_rechaza_notas_fuera_de_rango(grade_value):
    with pytest.raises(ValueError):
        Grade(
            id_grade=1,
            enrollment=make_enrollment(),
            grade1=grade_value,
            grade2=4.0,
            grade3=4.0,
            average=4.0,
            status=AcademicStatus.PASSED,
        )


def test_grade_rechaza_estado_academico_invalido():
    with pytest.raises(TypeError):
        Grade(
            id_grade=1,
            enrollment=make_enrollment(),
            grade1=4.0,
            grade2=4.0,
            grade3=4.0,
            average=4.0,
            status="passed",
        )


# ---------------------------------------------------------------------
# Pruebas de Receipt
# ---------------------------------------------------------------------

def test_receipt_valido_se_crea_correctamente():
    receipt = make_receipt()

    assert receipt.id_receipt == 1
    assert receipt.amount == 250000
    assert receipt.status == ReceiptStatus.PENDING
    assert str(receipt) == "Recibo 1 - pending"


def test_receipt_rechaza_monto_no_positivo():
    with pytest.raises(ValueError):
        Receipt(
            id_receipt=1,
            issue_date=date(2026, 1, 10),
            due_date=date(2026, 1, 20),
            amount=0,
            status=ReceiptStatus.PENDING,
            enrollment=make_enrollment(),
        )


def test_receipt_rechaza_fecha_vencimiento_anterior_a_emision():
    with pytest.raises(ValueError):
        Receipt(
            id_receipt=1,
            issue_date=date(2026, 1, 20),
            due_date=date(2026, 1, 10),
            amount=250000,
            status=ReceiptStatus.PENDING,
            enrollment=make_enrollment(),
        )


def test_receipt_rechaza_estado_invalido():
    with pytest.raises(TypeError):
        Receipt(
            id_receipt=1,
            issue_date=date(2026, 1, 10),
            due_date=date(2026, 1, 20),
            amount=250000,
            status="pending",
            enrollment=make_enrollment(),
        )


# ---------------------------------------------------------------------
# Pruebas de Payment
# ---------------------------------------------------------------------

def test_payment_valido_se_crea_correctamente():
    payment = Payment(
        id_payment=1,
        payment_date=date(2026, 1, 15),
        payment_method=PaymentMethod.CASH,
        receipt=make_receipt(),
    )

    assert payment.id_payment == 1
    assert payment.payment_method == PaymentMethod.CASH
    assert str(payment) == "Pago 1 - cash"


def test_payment_rechaza_fecha_invalida():
    with pytest.raises(TypeError):
        Payment(
            id_payment=1,
            payment_date="2026-01-15",
            payment_method=PaymentMethod.CASH,
            receipt=make_receipt(),
        )


def test_payment_rechaza_metodo_pago_invalido():
    with pytest.raises(TypeError):
        Payment(
            id_payment=1,
            payment_date=date(2026, 1, 15),
            payment_method="cash",
            receipt=make_receipt(),
        )


def test_payment_rechaza_receipt_invalido():
    with pytest.raises(TypeError):
        Payment(
            id_payment=1,
            payment_date=date(2026, 1, 15),
            payment_method=PaymentMethod.CASH,
            receipt="recibo inválido",
        )
