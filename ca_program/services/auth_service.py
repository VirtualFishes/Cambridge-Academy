import hashlib
from ca_program.models.user_model import UserModel
from ca_program.entities.user import User


class AuthService:
    """
    Servicio de autenticación del sistema.
    Gestiona la sesión activa y la verificación de credenciales con hash.
    """

    def __init__(self):
        self._user_model = UserModel()
        self._current_user: User | None = None

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------

    def authenticate(self, name: str, password: str) -> User | None:
        """
        Verifica las credenciales del usuario.
        Retorna el objeto User si son correctas, o None si fallan.
        """
        user = self._user_model.get_user_by_name(name)
        if user is None:
            return None

        hashed_input = self._hash_password(password)
        if user.password == hashed_input or user.password == password:
            self._current_user = user
            return user
        return None

    def logout(self):
        """Cierra la sesión actual."""
        self._current_user = None

    # ------------------------------------------------------------------
    # Sesión activa
    # ------------------------------------------------------------------

    def get_current_user(self) -> User | None:
        """Retorna el usuario con sesión activa."""
        return self._current_user

    def is_logged_in(self) -> bool:
        """Indica si hay un usuario con sesión iniciada."""
        return self._current_user is not None

    # ------------------------------------------------------------------
    # Permisos por rol
    # ------------------------------------------------------------------

    def is_admin(self) -> bool:
        return self._current_user is not None and self._current_user.role == "admin"

    def is_professor(self) -> bool:
        return self._current_user is not None and self._current_user.role == "professor"

    def is_student(self) -> bool:
        return self._current_user is not None and self._current_user.role == "student"

    def require_admin(self):
        """Lanza excepción si el usuario actual no es administrador."""
        if not self.is_admin():
            raise PermissionError("Se requieren permisos de administrador.")

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        """Genera un hash SHA-256 de la contraseña."""
        return hashlib.sha256(password.encode()).hexdigest()
