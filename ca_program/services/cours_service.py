import random
import string
from entities.course import Course

class CourseService:

    def __init__(self, model):
        # Conexión con el modelo
        self.model = model

    # Generar código numérico aleatorio
    def generate_code(self):
        return ''.join(random.choices(string.digits, k=6))

    # CREATE (crear curso)
    def create_course(self, name, quantity):
        if quantity < 0:
            raise ValueError("La cantidad no puede ser negativa")

        code = self.generate_code()

        # Asegurar que el código sea único
        while self.model.find_by_code(code):
            code = self.generate_code()

        course = Course(name, code, quantity)
        self.model.add_course(course)
        return course

    # READ (listar cursos)
    def show_courses(self):
        return self.model.get_all_courses()

    # READ (obtener uno)
    def get_course(self, code):
        return self.model.find_by_code(code)

    # UPDATE (actualizar curso)
    def update_course(self, code, new_name=None, new_quantity=None):
        course = self.model.find_by_code(code)
        if not course:
            return False

        if new_name:
            course.course_name = new_name

        if new_quantity is not None:
            if new_quantity < 0:
                raise ValueError("Cantidad inválida")
            course.quantity = new_quantity

        return True

    # DELETE (eliminar curso)
    def delete_course(self, code):
        return self.model.delete_course(code)