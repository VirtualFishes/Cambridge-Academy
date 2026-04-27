from ca_program.entities.user import User


class Student:
    def __init__(self, id_student: str, user: User):
        self.id_student = id_student
        self.user = user

    def __str__(self) -> str:
        return self.user.name
