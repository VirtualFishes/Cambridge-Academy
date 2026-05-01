"""
Servicio de autenticación.

Valida credenciales y retorna una respuesta segura para que la GUI decida la
navegación según el rol del usuario autenticado.
"""

from ca_program.models.user_model import UserModel
from ca_program.services import service_utils as utils


class LoginService:
    """Servicio encargado del inicio de sesión de usuarios."""

    @staticmethod
    def login(name: str, password: str) -> dict:
        """
        Autentica un usuario por nombre y contraseña.

        Retorna un diccionario con success, message, user y role. La validación
        de contraseña se delega a UserModel para mantener una sola fuente de
        verdad sobre cómo se comparan credenciales.
        """
        try:
            clean_name = str(name or "").strip()
            clean_password = str(password or "").strip()

            if not clean_name or not clean_password:
                return utils.error_response("Nombre de usuario y contraseña son obligatorios.")

            user = UserModel.get_user_by_name(clean_name)
            if not user:
                return utils.error_response("Usuario no encontrado")

            if not UserModel.validate_password(user, clean_password):
                return utils.error_response("Contraseña incorrecta")

            return utils.success_response(
                "Inicio de sesión exitoso",
                user=user,
                user_data=utils.user_to_dict(user),
                role=user.role.value,
            )

        except Exception as exc:
            return utils.unexpected_error_response(
                exc,
                "Ocurrió un error durante el inicio de sesión",
            )
