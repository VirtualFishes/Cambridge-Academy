def test_pago_exitoso(pago_service, inscripcion_service, estudiante_service, curso_service, profesor_service):
    estudiante_service.crear("1", "Ana", "ana@test.com", "123")
    profesor_service.crear("123", "Juan", "juan@test.com", "123")
    curso_service.crear("CURSO1", "123", 100)

    inscripcion = inscripcion_service.inscribir("1", "CURSO1")
    recibo_id = inscripcion["data"]["recibo_id"]

    result = pago_service.pagar(recibo_id, "EFECTIVO")
    assert result["success"] is True


def test_pago_duplicado(pago_service):
    recibo_id = "1"

    pago_service.pagar(recibo_id, "EFECTIVO")
    result = pago_service.pagar(recibo_id, "EFECTIVO")

    assert result["success"] is False