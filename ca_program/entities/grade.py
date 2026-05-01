"""
Entidad Grade.

Representa las notas asociadas a una matrícula. La entidad protege rangos
académicos básicos, mientras que el cálculo y registro siguen perteneciendo a los
modelos y servicios correspondientes.
"""

from dataclasses import dataclass

from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import AcademicStatus
from ca_program.entities._validators import (
    require_enum_member,
    require_instance,
    require_number_in_range,
    require_positive_integer,
)

MIN_GRADE = 0.0
MAX_GRADE = 5.0


@dataclass
class Grade:
    """Resultado académico de un estudiante dentro de una matrícula."""

    id_grade: int
    enrollment: Enrollment
    grade1: float
    grade2: float
    grade3: float
    average: float
    status: AcademicStatus

    def __post_init__(self) -> None:
        """Valida identificador, matrícula, notas, promedio y estado académico."""
        require_positive_integer(self.id_grade, "id_grade")
        require_instance(self.enrollment, Enrollment, "enrollment")
        require_number_in_range(self.grade1, "grade1", MIN_GRADE, MAX_GRADE)
        require_number_in_range(self.grade2, "grade2", MIN_GRADE, MAX_GRADE)
        require_number_in_range(self.grade3, "grade3", MIN_GRADE, MAX_GRADE)
        require_number_in_range(self.average, "average", MIN_GRADE, MAX_GRADE)
        require_enum_member(self.status, AcademicStatus, "status")

    def __str__(self) -> str:
        """Retorna una descripción legible del resultado académico."""
        return f"Nota {self.id_grade} - {self.enrollment.student.user.name} - {self.average}"
