def test_inscripcion_correcta(inscripcion_service, estudiante_service, curso_service, profesor_service):
    estudiante_service.crear("1", "Ana", "ana@test.com", "123")
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    curso_service.crear("CURSO1", "123", 100)

    result = inscripcion_service.inscribir("1", "CURSO1")
    assert result["success"] is True


def test_doble_inscripcion(inscripcion_service, estudiante_service, curso_service, profesor_service):
    estudiante_service.crear("1", "Ana", "ana@test.com", "123")
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    curso_service.crear("CURSO1", "123", 100)

    inscripcion_service.inscribir("1", "CURSO1")
    result = inscripcion_service.inscribir("1", "CURSO1")

    assert result["success"] is False