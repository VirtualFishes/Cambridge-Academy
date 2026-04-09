class CourseModel:
    def __init__(self):
        # Lista donde se almacenan los cursos
        self.courses = []

    # Agregar curso
    def add_course(self, course):
        self.courses.append(course)

    # Obtener todos los cursos
    def show_courses(self):
        return self.courses

    # Buscar curso por código
    def update_course(self, code):
        for course in self.courses:
            if course.code_course == code:
                return course
        return None

    # Eliminar curso
    def delete_course(self, code):
        course = self.find_by_code(code)
        if course:
            self.courses.remove(course)
            return True
        return False