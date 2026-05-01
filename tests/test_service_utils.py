from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from ca_program.entities.course import Course
from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import (
    AcademicStatus,
    PaymentMethod,
    ReceiptStatus,
    UserRole,
)
from ca_program.entities.payment import Payment
from ca_program.entities.professor import Professor
from ca_program.entities.receipt import Receipt
from ca_program.entities.student import Student
from ca_program.entities.user import User
from ca_program.services.service_utils import (
    academic_status_to_label,
    clean_optional_password,
    clean_text,
    course_to_dict,
    error_response,
    extract_id_value,
    extract_user_id,
    normalize_delete_payload,
    normalize_payload,
    normalize_spaces,
    parse_date,
    parse_float,
    parse_int,
    payment_to_dict,
    professor_to_dict,
    read_first,
    receipt_to_dict,
    response,
    role_matches,
    status_to_value,
    student_to_dict,
    success_response,
    unexpected_error_response,
    user_to_dict,
    validate_alpha_text,
    validate_email,
    validate_numeric_id,
    validate_password_required,
    validate_person_name,
    validate_required_fields,
    validate_required_id,
)


# ---------------------------------------------------------------------
# Fábricas de entidades válidas
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
    return Student(
        id_student="1001234567",
        user=make_user(role=UserRole.STUDENT),
    )


def make_professor():
    return Professor(
        id_professor="2001234567",
        professional_title="Licenciada en Inglés",
        user=make_user(
            id_user=2,
            name="Laura Gómez",
            role=UserRole.PROFESSOR,
            email="laura@example.com",
        ),
    )


def make_course():
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
        professor=make_professor(),
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


def make_payment():
    return Payment(
        id_payment=1,
        payment_date=date(2026, 1, 15),
        payment_method=PaymentMethod.CASH,
        receipt=make_receipt(),
    )


# ---------------------------------------------------------------------
# Normalización de payloads y lectura de valores
# ---------------------------------------------------------------------

def test_normalize_payload_combina_diccionario_y_kwargs():
    result = normalize_payload(
        data={"name": "Carlos", "email": "old@example.com"},
        kwargs={"email": "new@example.com", "role": "student"},
    )

    assert result == {
        "name": "Carlos",
        "email": "new@example.com",
        "role": "student",
    }


def test_normalize_payload_ignora_data_no_diccionario():
    assert normalize_payload(data="texto", kwargs={"name": "Carlos"}) == {"name": "Carlos"}


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"id": 5}, {"id": 5}),
        (7, {"id": 7}),
        ("ABC", {"id": "ABC"}),
        (None, {}),
        ("", {}),
    ],
)
def test_normalize_delete_payload_soporta_diccionario_o_id_directo(data, expected):
    assert normalize_delete_payload(data) == expected


def test_normalize_delete_payload_permite_cambiar_nombre_de_clave():
    result = normalize_delete_payload("ENG-A1", id_key="code_course")

    assert result == {"code_course": "ENG-A1"}


def test_read_first_retorna_primer_valor_no_vacio():
    payload = {"name": "", "email": None, "username": "admin"}

    assert read_first(payload, "name", "email", "username") == "admin"


def test_read_first_retorna_none_si_no_encuentra_valor_util():
    payload = {"name": "", "email": None}

    assert read_first(payload, "name", "email") is None


# ---------------------------------------------------------------------
# Limpieza y validación de texto
# ---------------------------------------------------------------------

def test_normalize_spaces_elimina_espacios_repetidos():
    assert normalize_spaces("  Cambridge    Academy   ") == "Cambridge Academy"


def test_normalize_spaces_convierte_none_en_cadena_vacia():
    assert normalize_spaces(None) == ""


def test_clean_text_limpia_texto_valido():
    assert clean_text("  Inglés   Básico ", "El nombre", min_length=3) == "Inglés Básico"


@pytest.mark.parametrize("value", [None, "", "  "])
def test_clean_text_rechaza_texto_vacio(value):
    with pytest.raises(ValueError):
        clean_text(value, "El campo", min_length=1)


def test_clean_text_rechaza_texto_menor_al_minimo():
    with pytest.raises(ValueError):
        clean_text("ab", "El campo", min_length=3)


def test_validate_required_fields_acepta_campos_presentes():
    validate_required_fields({"Nombre": "Carlos", "Correo": "carlos@example.com"})


def test_validate_required_fields_rechaza_campos_faltantes():
    with pytest.raises(ValueError) as exc_info:
        validate_required_fields({"Nombre": "", "Correo": None, "Rol": "student"})

    assert "Nombre" in str(exc_info.value)
    assert "Correo" in str(exc_info.value)


def test_validate_numeric_id_acepta_identificacion_numerica():
    assert validate_numeric_id(" 1001234567 ", "La identificación") == "1001234567"


@pytest.mark.parametrize("value", ["100ABC", "100-123", "abc"])
def test_validate_numeric_id_rechaza_valores_no_numericos(value):
    with pytest.raises(ValueError):
        validate_numeric_id(value, "La identificación")


def test_validate_numeric_id_rechaza_longitud_superior():
    with pytest.raises(ValueError):
        validate_numeric_id("123456", "La identificación", max_length=5)


def test_validate_person_name_acepta_tildes_espacios_y_guion():
    assert validate_person_name(" María-José Pérez ") == "María-José Pérez"


@pytest.mark.parametrize("value", ["Carlos123", "Miguel@Angel", "12345"])
def test_validate_person_name_rechaza_numeros_o_simbolos(value):
    with pytest.raises(ValueError):
        validate_person_name(value)


def test_validate_alpha_text_acepta_texto_alfabetico():
    assert validate_alpha_text(" Colombiana ", "La nacionalidad") == "Colombiana"


@pytest.mark.parametrize("value", ["Colombia2", "Colombia@"])
def test_validate_alpha_text_rechaza_numeros_o_simbolos(value):
    with pytest.raises(ValueError):
        validate_alpha_text(value, "La nacionalidad")


def test_validate_password_required_acepta_password_valida():
    assert validate_password_required(" 1234 ") == "1234"


@pytest.mark.parametrize("password", [None, "", "123"])
def test_validate_password_required_rechaza_password_invalida(password):
    with pytest.raises(ValueError):
        validate_password_required(password)


@pytest.mark.parametrize(
    "email",
    ["admin@example.com", "usuario.nombre@dominio.co"],
)
def test_validate_email_acepta_formato_valido(email):
    assert validate_email(email) == email


@pytest.mark.parametrize(
    "email",
    ["correo", "usuario@", "@dominio.com", "usuario dominio@example.com"],
)
def test_validate_email_rechaza_formato_invalido(email):
    with pytest.raises(ValueError):
        validate_email(email)


def test_clean_optional_password_retorna_none_si_no_se_envia_password():
    assert clean_optional_password(None) is None
    assert clean_optional_password("") is None
    assert clean_optional_password("   ") is None


def test_clean_optional_password_limpia_password_valida():
    assert clean_optional_password(" 1234 ") == "1234"


def test_clean_optional_password_rechaza_password_corta():
    with pytest.raises(ValueError):
        clean_optional_password("123")


# ---------------------------------------------------------------------
# Conversión de fechas y números
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "value,expected",
    [
        ("2026-01-15", date(2026, 1, 15)),
        ("15/01/2026", date(2026, 1, 15)),
        ("15-01-2026", date(2026, 1, 15)),
        (datetime(2026, 1, 15, 8, 30), date(2026, 1, 15)),
        (date(2026, 1, 15), date(2026, 1, 15)),
    ],
)
def test_parse_date_acepta_formatos_validos(value, expected):
    assert parse_date(value, "Fecha inválida") == expected


def test_parse_date_rechaza_formato_invalido():
    with pytest.raises(ValueError):
        parse_date("01.15.2026", "Fecha inválida")


def test_parse_date_rechaza_fecha_futura_cuando_no_se_permite():
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValueError):
        parse_date(tomorrow, "Fecha inválida", allow_future=False)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("4.5", 4.5),
        ("4,5", 4.5),
        (5, 5.0),
    ],
)
def test_parse_float_convierte_valores_validos(value, expected):
    assert parse_float(value, "Número inválido") == expected


def test_parse_float_rechaza_valor_no_numerico():
    with pytest.raises(ValueError):
        parse_float("abc", "Número inválido")


@pytest.mark.parametrize("value", [-1, 6])
def test_parse_float_valida_limites(value):
    with pytest.raises(ValueError):
        parse_float(value, "Número inválido", minimum=0, maximum=5)


@pytest.mark.parametrize(
    "value,expected",
    [("10", 10), (10, 10)],
)
def test_parse_int_convierte_valores_validos(value, expected):
    assert parse_int(value, "Entero inválido") == expected


def test_parse_int_rechaza_valor_no_entero():
    with pytest.raises(ValueError):
        parse_int("10.5", "Entero inválido")


@pytest.mark.parametrize("value", [0, 101])
def test_parse_int_valida_limites(value):
    with pytest.raises(ValueError):
        parse_int(value, "Entero inválido", minimum=1, maximum=100)


# ---------------------------------------------------------------------
# Extracción y validación de identificadores
# ---------------------------------------------------------------------

def test_extract_id_value_extrae_id_desde_diccionario():
    assert extract_id_value({"id_student": "1001234567"}) == "1001234567"


def test_extract_id_value_extrae_id_desde_objeto():
    obj = SimpleNamespace(id_user=10)

    assert extract_id_value(obj) == 10


def test_extract_id_value_retorna_valor_directo_si_no_es_dict_ni_objeto():
    assert extract_id_value("ENG-A1") == "ENG-A1"


def test_validate_required_id_acepta_id_directo():
    assert validate_required_id(" ENG-A1 ", "El curso es obligatorio.") == "ENG-A1"


@pytest.mark.parametrize("value", [None, "", {"id": ""}])
def test_validate_required_id_rechaza_id_faltante(value):
    with pytest.raises(ValueError):
        validate_required_id(value, "El identificador es obligatorio.")


@pytest.mark.parametrize(
    "user,id_user,expected",
    [
        (None, 5, 5),
        ({"id_user": "6"}, None, 6),
        (SimpleNamespace(id_user="7"), None, 7),
        ("8", None, 8),
    ],
)
def test_extract_user_id_obtiene_id_valido(user, id_user, expected):
    assert extract_user_id(user=user, id_user=id_user) == expected


@pytest.mark.parametrize("value", [None, "", "abc", 0, -1])
def test_extract_user_id_rechaza_id_invalido(value):
    with pytest.raises(ValueError):
        extract_user_id(id_user=value)


# ---------------------------------------------------------------------
# Roles, estados y respuestas
# ---------------------------------------------------------------------

def test_role_matches_acepta_rol_por_valor_o_nombre():
    user = make_user(role=UserRole.ADMIN)

    assert role_matches(user, ["admin"])
    assert role_matches(user, ["administrator"])


def test_role_matches_funciona_con_diccionario():
    assert role_matches({"role": "student"}, ["student"])


def test_role_matches_respeta_allow_missing():
    assert role_matches(None, ["admin"], allow_missing=True) is True
    assert role_matches(None, ["admin"], allow_missing=False) is False


def test_role_matches_rechaza_rol_no_permitido():
    assert role_matches({"role": "student"}, ["admin"]) is False


def test_status_to_value_convierte_enum_a_valor():
    assert status_to_value(AcademicStatus.PASSED) == "passed"


@pytest.mark.parametrize(
    "status,expected",
    [
        (AcademicStatus.PASSED, "Aprobado"),
        (AcademicStatus.FAILED, "Reprobado"),
        ("pending", "Pendiente"),
        ("unknown", "Sin estado"),
    ],
)
def test_academic_status_to_label_convierte_estado_a_etiqueta(status, expected):
    assert academic_status_to_label(status) == expected


def test_response_construye_diccionario_homogeneo():
    result = response(True, "Correcto", data={"id": 1})

    assert result == {"success": True, "message": "Correcto", "data": {"id": 1}}


def test_success_response_construye_respuesta_exitosa():
    assert success_response("Guardado", id=1) == {
        "success": True,
        "message": "Guardado",
        "id": 1,
    }


def test_error_response_construye_respuesta_de_error():
    assert error_response("Error", field="name") == {
        "success": False,
        "message": "Error",
        "field": "name",
    }


def test_unexpected_error_response_retorna_mensaje_seguro(capsys):
    result = unexpected_error_response(
        RuntimeError("Detalle técnico"),
        "Ocurrió un error controlado",
    )

    captured = capsys.readouterr()

    assert "Detalle técnico" in captured.out
    assert result == {
        "success": False,
        "message": "Ocurrió un error controlado",
    }


# ---------------------------------------------------------------------
# Conversión de entidades a diccionarios
# ---------------------------------------------------------------------

def test_user_to_dict_convierte_usuario():
    user = make_user(role=UserRole.ADMIN)

    result = user_to_dict(user)

    assert result["id_user"] == 1
    assert result["name"] == "Carlos Pérez"
    assert result["role"] == "administrator"
    assert result["email"] == "carlos@example.com"


def test_user_to_dict_retorna_diccionario_vacio_si_user_es_none():
    assert user_to_dict(None) == {}


def test_student_to_dict_convierte_estudiante():
    result = student_to_dict(make_student())

    assert result["id_student"] == "1001234567"
    assert result["id_user"] == 1
    assert result["name"] == "Carlos Pérez"


def test_professor_to_dict_convierte_profesor():
    result = professor_to_dict(make_professor())

    assert result["id_professor"] == "2001234567"
    assert result["professional_title"] == "Licenciada en Inglés"
    assert result["name"] == "Laura Gómez"


def test_course_to_dict_convierte_curso_con_profesor():
    result = course_to_dict(make_course())

    assert result["code_course"] == "ENG-A1"
    assert result["name"] == "Inglés A1"
    assert result["price"] == 250000
    assert result["id_professor"] == "2001234567"
    assert result["professor"]["name"] == "Laura Gómez"
    assert result["students"] == 0
    assert result["enrolled_students"] == 0


def test_receipt_to_dict_convierte_recibo():
    result = receipt_to_dict(make_receipt())

    assert result["id_receipt"] == 1
    assert result["amount"] == 250000
    assert result["status"] == "pending"
    assert result["enrollment"]["student"]["id_student"] == "1001234567"
    assert result["enrollment"]["course"]["code_course"] == "ENG-A1"


def test_payment_to_dict_convierte_pago():
    result = payment_to_dict(make_payment())

    assert result["id_payment"] == 1
    assert result["payment_date"] == date(2026, 1, 15)
    assert result["payment_method"] == "cash"
    assert result["receipt"]["id_receipt"] == 1


@pytest.mark.parametrize(
    "converter",
    [
        student_to_dict,
        professor_to_dict,
        course_to_dict,
        receipt_to_dict,
        payment_to_dict,
    ],
)
def test_converters_retornan_diccionario_vacio_si_reciben_none(converter):
    assert converter(None) == {}
