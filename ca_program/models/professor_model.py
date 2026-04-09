class ProfessorModel:
    def __init__(self):
        # Lista donde se almacenan los profesores
        self.professors = []

    # Agregar profesor
    def add_professor(self, professor):
        self.professors.append(professor)

    # Obtener todos los profesores
    def get_all_professors(self):
        return self.professors

    # Buscar profesor por código
    def find_by_code(self, code):
        for professor in self.professors:
            if professor.code == code:
                return professor
        return None

    # Eliminar profesor
    def delete_professor(self, code):
        professor = self.find_by_code(code)
        if professor:
            self.professors.remove(professor)
            return True
        return False