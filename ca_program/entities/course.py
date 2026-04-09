class Course:
    def __init__(self, course_name, code_course, quantity):
        self.course_name = course_name
        self.code_course = code_course
        self.quantity = quantity

    def __str__(self):
        return f"{self.course_name} | Código: {self.code_course} | Cantidad: {self.quantity}"