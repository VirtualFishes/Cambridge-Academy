def test_cambio_password_correcto(account_service):
    result = account_service.cambiar_password("user1", "old123", "new123", "new123")
    assert result["success"] is True


def test_password_actual_incorrecta(account_service):
    result = account_service.cambiar_password("user1", "wrong", "new123", "new123")
    assert result["success"] is False


def test_confirmacion_incorrecta(account_service):
    result = account_service.cambiar_password("user1", "old123", "new123", "xxx")
    assert result["success"] is False