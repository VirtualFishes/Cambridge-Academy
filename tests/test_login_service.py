from datetime import date

import pytest

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.user import User
from ca_program.services.login_service import LoginService


def make_user(
    id_user=1,
    name="Admin Principal",
    password="1234",
    role=UserRole.ADMIN,
    email="admin@example.com",
    birth_date=date(1990, 1, 15),
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


# ---------------------------------------------------------------------
# Pruebas de campos obligatorios
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "name,password",
    [
        ("", "1234"),
        ("admin", ""),
        ("", ""),
        (None, "1234"),
        ("admin", None),
        ("   ", "1234"),
        ("admin", "   "),
    ],
)
def test_login_rechaza_campos_obligatorios(mocker, name, password):
    mock_get_user = mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name"
    )

    result = LoginService.login(name, password)

    assert result["success"] is False
    assert result["message"] == "Nombre de usuario y contraseña son obligatorios."
    mock_get_user.assert_not_called()


# ---------------------------------------------------------------------
# Pruebas de usuario no encontrado
# ---------------------------------------------------------------------

def test_login_rechaza_usuario_no_encontrado(mocker):
    mock_get_user = mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name",
        return_value=None,
    )

    mock_validate_password = mocker.patch(
        "ca_program.services.login_service.UserModel.validate_password"
    )

    result = LoginService.login("usuario_inexistente", "1234")

    assert result["success"] is False
    assert result["message"] == "Usuario no encontrado"

    mock_get_user.assert_called_once_with("usuario_inexistente")
    mock_validate_password.assert_not_called()


# ---------------------------------------------------------------------
# Pruebas de contraseña incorrecta
# ---------------------------------------------------------------------

def test_login_rechaza_password_incorrecto(mocker):
    user = make_user()

    mock_get_user = mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name",
        return_value=user,
    )

    mock_validate_password = mocker.patch(
        "ca_program.services.login_service.UserModel.validate_password",
        return_value=False,
    )

    result = LoginService.login("Admin Principal", "password_malo")

    assert result["success"] is False
    assert result["message"] == "Contraseña incorrecta"

    mock_get_user.assert_called_once_with("Admin Principal")
    mock_validate_password.assert_called_once_with(user, "password_malo")


# ---------------------------------------------------------------------
# Pruebas de login exitoso
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "role",
    [
        UserRole.ADMIN,
        UserRole.PROFESSOR,
        UserRole.STUDENT,
    ],
)
def test_login_exitoso_retorna_usuario_rol_y_datos(mocker, role):
    user = make_user(role=role)

    mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name",
        return_value=user,
    )

    mocker.patch(
        "ca_program.services.login_service.UserModel.validate_password",
        return_value=True,
    )

    result = LoginService.login("Admin Principal", "1234")

    assert result["success"] is True
    assert result["message"] == "Inicio de sesión exitoso"
    assert result["user"] is user
    assert result["role"] == role.value

    assert result["user_data"]["id_user"] == user.id_user
    assert result["user_data"]["name"] == user.name
    assert result["user_data"]["role"] == role.value
    assert result["user_data"]["email"] == user.email
    assert result["user_data"]["nationality"] == user.nationality


def test_login_limpia_espacios_antes_de_validar(mocker):
    user = make_user()

    mock_get_user = mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name",
        return_value=user,
    )

    mock_validate_password = mocker.patch(
        "ca_program.services.login_service.UserModel.validate_password",
        return_value=True,
    )

    result = LoginService.login("   Admin Principal   ", "   1234   ")

    assert result["success"] is True
    mock_get_user.assert_called_once_with("Admin Principal")
    mock_validate_password.assert_called_once_with(user, "1234")


# ---------------------------------------------------------------------
# Pruebas de errores inesperados
# ---------------------------------------------------------------------

def test_login_maneja_error_inesperado_al_buscar_usuario(mocker):
    mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name",
        side_effect=RuntimeError("Error técnico de base de datos"),
    )

    result = LoginService.login("admin", "1234")

    assert result["success"] is False
    assert result["message"] == "Ocurrió un error durante el inicio de sesión"


def test_login_maneja_error_inesperado_al_validar_password(mocker):
    user = make_user()

    mocker.patch(
        "ca_program.services.login_service.UserModel.get_user_by_name",
        return_value=user,
    )

    mocker.patch(
        "ca_program.services.login_service.UserModel.validate_password",
        side_effect=RuntimeError("Error técnico validando contraseña"),
    )

    result = LoginService.login("admin", "1234")

    assert result["success"] is False
    assert result["message"] == "Ocurrió un error durante el inicio de sesión"
