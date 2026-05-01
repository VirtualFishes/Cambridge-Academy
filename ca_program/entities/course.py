"""
Entidad Course.

Define la información académica y administrativa de un curso ofertado por la
academia. No registra cursos en base de datos ni decide procesos de inscripción.
"""

from dataclasses import dataclass
from datetime import date

from ca_program.entities.professor import Professor
from ca_program.entities._validators import (
    require_date_order,
    require_instance,
    require_non_empty_string,
    require_positive_integer,
    require_positive_number,
)


@dataclass
class Course:
    """Curso académico asignado a un profesor."""

    code_course: str | int
    name: str
    description: str
    price: float
    duration_days: int
    intensity_hours: int
    schedule: str
    location: str
    start_date: date
    end_date: date
    professor: Professor

    def __post_init__(self) -> None:
        """Valida los datos esenciales para que el curso sea coherente."""
        # PostgreSQL puede retornar code_course como entero cuando la columna
        # es serial/integer. La entidad lo normaliza a texto porque la GUI y
        # los servicios lo manejan como identificador visible del curso.
        self.code_course = "" if self.code_course is None else str(self.code_course).strip()
        require_non_empty_string(self.code_course, "code_course")
        require_non_empty_string(self.name, "name")
        require_non_empty_string(self.description, "description")
        require_positive_number(self.price, "price")
        require_positive_integer(self.duration_days, "duration_days")
        require_positive_integer(self.intensity_hours, "intensity_hours")
        require_non_empty_string(self.schedule, "schedule")
        require_non_empty_string(self.location, "location")
        require_date_order(self.start_date, self.end_date, "start_date", "end_date")
        require_instance(self.professor, Professor, "professor")

    def __str__(self) -> str:
        """Retorna el nombre visible del curso."""
        return self.name
