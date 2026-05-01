"""
Entidad Professor.

Representa a un profesor de la academia. Su información de identificación y
acceso se delega a User, manteniendo aquí solo los datos propios del rol docente.
"""

from dataclasses import dataclass

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.user import User
from ca_program.entities._validators import require_instance, require_non_empty_string


@dataclass
class Professor:
    """Profesor responsable de orientar uno o más cursos."""

    id_professor: str
    professional_title: str
    user: User

    def __post_init__(self) -> None:
        """Valida la identidad docente y su relación con un usuario profesor."""
        require_non_empty_string(self.id_professor, "id_professor")
        require_non_empty_string(self.professional_title, "professional_title")
        require_instance(self.user, User, "user")

        if self.user.role is not UserRole.PROFESSOR:
            raise ValueError("user.role debe corresponder a UserRole.PROFESSOR.")

    def __str__(self) -> str:
        """Retorna el nombre visible del profesor."""
        return self.user.name
