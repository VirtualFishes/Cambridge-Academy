from ca_program.services.auth_service import AuthService
from ca_program.entities.user import User


class LoginService:
    """
    Servicio que expone la lógica de inicio de sesión a la capa de vista.
    Actúa como intermediario entre login_gui y AuthService.
    """

    def __init__(self, auth_service: AuthService):
        self._auth = auth_service

    def login(self, name: str, password: str) -> tuple[bool, str, User | None]:
        """
        Intenta iniciar sesión con las credenciales dadas.

        Retorna:
            (True, "", User)          → Login exitoso
            (False, mensaje, None)    → Login fallido con razón
        """
        name = name.strip()
        password = password.strip()

        if not name or not password:
            return False, "Por favor completa todos los campos.", None

        user = self._auth.authenticate(name, password)

        if user is None:
            return False, "Usuario o contraseña incorrectos.", None

        return True, "", user

    def get_redirect_view(self, user: User) -> str:
        """
        Determina a qué vista redirigir al usuario según su rol.

        Retorna:
            'admin'     → Panel de administración
            'professor' → Panel del profesor
            'student'   → Panel del estudiante
            'unknown'   → Vista por defecto
        """
        return user.role if user.role in ("admin", "professor", "student") else "unknown"
