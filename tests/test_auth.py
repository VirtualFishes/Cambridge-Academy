def test_login_campos_vacios(auth_service):
    result = auth_service.login("", "")
    assert result["success"] is False


def test_login_password_incorrecta(auth_service):
    result = auth_service.login("admin", "wrong")
    assert result["success"] is False


def test_login_usuario_inexistente(auth_service):
    result = auth_service.login("no_user", "123")
    assert result["success"] is False


def test_login_admin_correcto(auth_service):
    result = auth_service.login("admin", "admin123")
    assert result["success"] is True
    assert result["role"] == "ADMIN"


def test_login_estudiante_correcto(auth_service):
    result = auth_service.login("student", "123")
    assert result["success"] is True
    assert result["role"] == "STUDENT"