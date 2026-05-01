"""
Entidad Enrollment.

Representa la matrícula de un estudiante en un curso. Su responsabilidad se
limita a conservar esa asociación dentro del dominio académico.
"""

from dataclasses import dataclass

from ca_program.entities.course import Course
from ca_program.entities.student import Student
from ca_program.entities._validators import require_instance, require_positive_integer


@dataclass
class Enrollment:
    """Relación formal entre un estudiante y un curso."""

    id_enrollment: int
    student: Student
    course: Course

    def __post_init__(self) -> None:
        """Valida que la matrícula vincule entidades existentes y correctas."""
        require_positive_integer(self.id_enrollment, "id_enrollment")
        require_instance(self.student, Student, "student")
        require_instance(self.course, Course, "course")

    def __str__(self) -> str:
        """Retorna una descripción legible de la matrícula."""
        return f"{self.student.user.name} - {self.course.name}"
