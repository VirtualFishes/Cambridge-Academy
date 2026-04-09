import random
import string
from entities.professor import Professor

class ProfessorService:

    def __init__(self, model):
        # Conexión con el modelo
        self.model = model

    # Generar código numérico de 9 dígitos
    def generate_code(self):
        return ''.join(random.choices(string.digits, k=9))

    # CREATE (crear profesor)
    def create_professor(self, name, document, birthdate, phone, email):
        code = self.generate_code()

        # Asegurar que el código sea único
        while self.model.find_by_code(code):
            code = self.generate_code()

        professor = Professor(name, code, document, birthdate, phone, email)
        self.model.add_professor(professor)
        return professor

    # READ (listar profesores)
    def show_professors(self):
        return self.model.get_all_professors()

    # READ (obtener uno)
    def get_professor(self, code):
        return self.model.find_by_code(code)

    # UPDATE (actualizar profesor)
    def update_professor(self, code, name=None, document=None, birthdate=None, phone=None, email=None):
        professor = self.model.find_by_code(code)
        if not professor:
            return False

        if name:
            professor.name = name
        if document:
            professor.document = document
        if birthdate:
            professor.birthdate = birthdate
        if phone:
            professor.phone = phone
        if email:
            professor.email = email

        return True

    # DELETE (eliminar profesor)
    def delete_professor(self, code):
        return self.model.delete_professor(code)