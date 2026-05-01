"""
Entidad Student.

Representa a un estudiante de la academia. Mantiene la relación con User porque
los datos personales y de acceso viven en la cuenta base del sistema.
"""

from dataclasses import dataclass

from ca_program.entities.fixed_values import UserRole
from ca_program.entities.user import User
from ca_program.entities._validators import require_instance, require_non_empty_string


@dataclass
class Student:
    """Estudiante inscrito o disponible para inscripción en cursos."""

    id_student: str
    user: User

    def __post_init__(self) -> None:
        """Valida que el estudiante tenga identificador propio y usuario válido."""
        require_non_empty_string(self.id_student, "id_student")
        require_instance(self.user, User, "user")

        if self.user.role is not UserRole.STUDENT:
            raise ValueError("user.role debe corresponder a UserRole.STUDENT.")

    def __str__(self) -> str:
        """Retorna el nombre visible del estudiante."""
        return self.user.name
