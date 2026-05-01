"""
Servicio de cuenta de usuario.

Centraliza operaciones del usuario autenticado que no pertenecen a una entidad
académica concreta. Actualmente soporta HU-30: cambio de contraseña.
"""

from ca_program.models.user_model import UserModel
from ca_program.services.service_utils import error_response, success_response, unexpected_error_response


class AccountService:
    """Servicio encargado de operaciones privadas de la cuenta autenticada."""

    MIN_PASSWORD_LENGTH = 4

    @staticmethod
    def change_password(
        id_user: int,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> dict:
        """
        Cambia la contraseña del usuario autenticado.

        La validación se hace antes de persistir cambios para evitar estados
        inválidos. La comparación contra la contraseña actual se delega al
        UserModel, conservando la separación entre servicio y modelo.
        """
        try:
            clean_current_password = AccountService._clean_password(current_password)
            clean_new_password = AccountService._clean_password(new_password)
            clean_confirm_password = AccountService._clean_password(confirm_password)

            validation = AccountService._validate_password_input(
                current_password=clean_current_password,
                new_password=clean_new_password,
                confirm_password=clean_confirm_password,
            )
            if not validation["success"]:
                return validation

            user = UserModel.get_user_by_id(id_user)
            if not user:
                return error_response("No se encontró el usuario autenticado.")

            if not UserModel.validate_password(user, clean_current_password):
                return error_response("La contraseña actual no es correcta.")

            if UserModel.validate_password(user, clean_new_password):
                return error_response("La nueva contraseña no puede ser igual a la actual.")

            updated = UserModel.update_password(
                id_user=id_user,
                new_password=clean_new_password,
            )
            if not updated:
                return error_response("No fue posible actualizar la contraseña.")

            return success_response("Contraseña actualizada correctamente.")

        except Exception as exc:
            return unexpected_error_response(
                exc,
                "Ocurrió un error al cambiar la contraseña.",
            )

    @staticmethod
    def _validate_password_input(
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> dict:
        """Valida obligatoriedad, longitud mínima y confirmación de contraseña."""
        if not current_password or not new_password or not confirm_password:
            return error_response("Todos los campos son obligatorios.")

        if len(new_password) < AccountService.MIN_PASSWORD_LENGTH:
            return error_response(
                "La nueva contraseña debe tener al menos "
                f"{AccountService.MIN_PASSWORD_LENGTH} caracteres."
            )

        if new_password != confirm_password:
            return error_response("La nueva contraseña y su confirmación no coinciden.")

        return success_response("Validación correcta.")

    @staticmethod
    def _clean_password(value: str | None) -> str:
        """Normaliza el texto de contraseña recibido desde la interfaz."""
        return (value or "").strip()
