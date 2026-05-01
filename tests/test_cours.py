def test_crear_curso_valido(curso_service, profesor_service):
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    result = curso_service.crear("CURSO1", "123", 100)
    assert result["success"] is True


def test_curso_codigo_duplicado(curso_service, profesor_service):
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    curso_service.crear("CURSO1", "123", 100)

    result = curso_service.crear("CURSO1", "123", 200)
    assert result["success"] is False


def test_curso_profesor_inexistente(curso_service):
    result = curso_service.crear("CURSO1", "999", 100)
    assert result["success"] is False