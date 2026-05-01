from ca_program.models.user_model import UserModel


class AccountService:
    """
    Servicio encargado de las operaciones de cuenta del usuario autenticado.

    HU-30: Cambiar contraseña.
    """

    MIN_PASSWORD_LENGTH = 4

    @staticmethod
    def change_password(
        id_user: int,
        current_password: str,
        new_password: str,
        confirm_password: str
    ) -> dict:
        """
        Cambia la contraseña del usuario autenticado.

        Retorna un diccionario con:
        - success: bool
        - message: str
        """
        try:
            current_password = (current_password or "").strip()
            new_password = (new_password or "").strip()
            confirm_password = (confirm_password or "").strip()

            validation = AccountService._validate_password_input(
                current_password=current_password,
                new_password=new_password,
                confirm_password=confirm_password
            )

            if not validation["success"]:
                return validation

            user = UserModel.get_user_by_id(id_user)

            if not user:
                return {
                    "success": False,
                    "message": "No se encontró el usuario autenticado."
                }

            if not UserModel.validate_password(user, current_password):
                return {
                    "success": False,
                    "message": "La contraseña actual no es correcta."
                }

            if UserModel.validate_password(user, new_password):
                return {
                    "success": False,
                    "message": "La nueva contraseña no puede ser igual a la actual."
                }

            updated = UserModel.update_password(
                id_user=id_user,
                new_password=new_password
            )

            if not updated:
                return {
                    "success": False,
                    "message": "No fue posible actualizar la contraseña."
                }

            return {
                "success": True,
                "message": "Contraseña actualizada correctamente."
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error al cambiar la contraseña."
            }

    @staticmethod
    def _validate_password_input(
        current_password: str,
        new_password: str,
        confirm_password: str
    ) -> dict:
        if not current_password or not new_password or not confirm_password:
            return {
                "success": False,
                "message": "Todos los campos son obligatorios."
            }

        if len(new_password) < AccountService.MIN_PASSWORD_LENGTH:
            return {
                "success": False,
                "message": (
                    "La nueva contraseña debe tener al menos "
                    f"{AccountService.MIN_PASSWORD_LENGTH} caracteres."
                )
            }

        if new_password != confirm_password:
            return {
                "success": False,
                "message": "La nueva contraseña y su confirmación no coinciden."
            }

        return {
            "success": True,
            "message": "Validación correcta."
        }
