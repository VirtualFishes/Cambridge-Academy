from ca_program.entities.enrollment import Enrollment
from ca_program.entities.fixed_values import AcademicStatus


class Grade:
    def __init__(
        self,
        id_grade: int,
        enrollment: Enrollment,
        grade1: float,
        grade2: float,
        grade3: float,
        average: float,
        status: AcademicStatus,
    ):
        self.id_grade = id_grade
        self.enrollment = enrollment
        self.grade1 = grade1
        self.grade2 = grade2
        self.grade3 = grade3
        self.average = average
        self.status = status

    def __str__(self) -> str:
        return f"Nota {self.id_grade} - {self.enrollment.student.user.name} - {self.average}"
