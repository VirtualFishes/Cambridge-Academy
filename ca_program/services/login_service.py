from ca_program.models.user_model import UserModel


class LoginService:

    @staticmethod
    def login(name: str, password: str) -> dict:
        """
        Realiza el proceso de autenticación de un usuario.

        Retorna un diccionario con:
        - success: bool
        - message: str
        - user: User (opcional)
        - role: str (opcional)
        """

        try:
            user = UserModel.get_user_by_name(name)

            # Usuario no existe
            if not user:
                return {
                    "success": False,
                    "message": "Usuario no encontrado"
                }

            # Contraseña incorrecta
            if not UserModel.validate_password(user, password):
                return {
                    "success": False,
                    "message": "Contraseña incorrecta"
                }

            # Login exitoso
            return {
                "success": True,
                "message": "Inicio de sesión exitoso",
                "user": user,
                "role": user.role.value  # útil para redirección en la GUI
            }

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": "Ocurrió un error durante el inicio de sesión"
            }
