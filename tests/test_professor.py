def test_crear_profesor_valido(profesor_service):
    result = profesor_service.crear("123", "Juan", "juan@test.com", "123")
    assert result["success"] is True


def test_crear_profesor_id_duplicada(profesor_service):
    profesor_service.crear("123", "Juan", "a@test.com", "123")
    result = profesor_service.crear("123", "Pedro", "b@test.com", "123")
    assert result["success"] is False


def test_actualizar_profesor(profesor_service):
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    result = profesor_service.actualizar("123", nombre="Carlos")
    assert result["success"] is True


def test_eliminar_profesor_sin_cursos(profesor_service):
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    result = profesor_service.eliminar("123")
    assert result["success"] is True