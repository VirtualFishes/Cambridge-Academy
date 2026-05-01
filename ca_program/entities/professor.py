from ca_program.entities.user import User


class Professor:
    def __init__(self, id_professor: str, professional_title: str, user: User):
        self.id_professor = id_professor
        self.professional_title = professional_title
        self.user = user

    def __str__(self) -> str:
        return self.user.name
