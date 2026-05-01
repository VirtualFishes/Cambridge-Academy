"""
Entidad User.

Representa la cuenta base de acceso al sistema. Esta entidad conserva únicamente
los datos comunes de cualquier usuario, sin autenticar, consultar base de datos ni
definir flujos de interfaz.
"""

from dataclasses import dataclass
from datetime import date

from ca_program.entities.fixed_values import UserRole
from ca_program.entities._validators import (
    require_date,
    require_enum_member,
    require_non_empty_string,
    require_positive_integer,
)


@dataclass
class User:
    """Cuenta de usuario registrada en el sistema académico."""

    id_user: int
    name: str
    password: str
    role: UserRole
    email: str
    birth_date: date
    nationality: str

    def __post_init__(self) -> None:
        """Protege la consistencia mínima de los datos de usuario."""
        require_positive_integer(self.id_user, "id_user")
        require_non_empty_string(self.name, "name")
        require_non_empty_string(self.password, "password")
        require_enum_member(self.role, UserRole, "role")
        require_non_empty_string(self.email, "email")
        require_date(self.birth_date, "birth_date")
        require_non_empty_string(self.nationality, "nationality")

        if "@" not in self.email or self.email.startswith("@") or self.email.endswith("@"):
            raise ValueError("email debe tener un formato básico válido.")

    def __str__(self) -> str:
        """Retorna el nombre visible del usuario."""
        return self.name
