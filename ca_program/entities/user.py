from datetime import date
from ca_program.entities.fixed_values import UserRole

class User:
    def __init__(
        self,
        id_user: int,
        name: str,
        password: str,
        role: UserRole,
        email: str,
        birth_date: date,
        nationality: str
    ):
        self.id_user = id_user
        self.name = name
        self.password = password
        self.role = role
        self.email = email
        self.birth_date = birth_date
        self.nationality = nationality

    def __str__(self) -> str:
        return (self.name)
