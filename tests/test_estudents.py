def test_crear_estudiante_valido(estudiante_service):
    result = estudiante_service.crear("1", "Ana", "ana@test.com", "123")
    assert result["success"] is True


def test_crear_estudiante_duplicado(estudiante_service):
    estudiante_service.crear("1", "Ana", "a@test.com", "123")
    result = estudiante_service.crear("1", "Ana2", "b@test.com", "123")
    assert result["success"] is False


def test_eliminar_estudiante(estudiante_service):
    estudiante_service.crear("1", "Ana", "ana@test.com", "123")
    result = estudiante_service.eliminar("1")
    assert result["success"] is True