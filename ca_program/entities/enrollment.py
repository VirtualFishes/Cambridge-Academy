from ca_program.entities.student import Student
from ca_program.entities.course import Course


class Enrollment:
    def __init__(self, id_enrollment: int, student: Student, course: Course):
        self.id_enrollment = id_enrollment
        self.student = student
        self.course = course

    def __str__(self) -> str:
        return f"{self.student.user.name} - {self.course.name}"
