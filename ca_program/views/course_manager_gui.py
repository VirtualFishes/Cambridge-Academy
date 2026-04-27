from ca_program.views.admin_base_manager_gui import AdminCrudWidget, FieldSpec


class CourseManagerWidget(AdminCrudWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Gestión de cursos",
            description="Registro y consulta de cursos según HU-06 y HU-07.",
            service_module="ca_program.services.course_service",
            service_class="CourseService",
            create_method_names=["register_course", "create_course", "add_course", "save_course", "register"],
            list_method_names=["get_courses", "list_courses", "get_all_courses", "consult_courses", "get_all"],
            fields=[
                FieldSpec("name", "Nombre", "Nombre del curso"),
                FieldSpec("description", "Descripción", "Contenido o propósito del curso", "textarea"),
                FieldSpec("price", "Precio", field_type="float", minimum=0, maximum=100000000),
                FieldSpec("duration_days", "Duración días", field_type="int", minimum=1, maximum=3650, default=30),
                FieldSpec("intensity_hours", "Intensidad horas", field_type="int", minimum=1, maximum=5000, default=40),
                FieldSpec("schedule", "Horario", "Ej: Lunes y miércoles 6:00 p.m."),
                FieldSpec("location", "Ubicación", "Aula, sede o modalidad"),
                FieldSpec("start_date", "Fecha inicio", field_type="date"),
                FieldSpec("end_date", "Fecha fin", field_type="date"),
                FieldSpec("id_professor", "Profesor asignado", "Identificación del profesor"),
            ],
            table_columns=[
                ("Código", "code_course"),
                ("Nombre", "name"),
                ("Precio", "price"),
                ("Duración", "duration_days"),
                ("Intensidad", "intensity_hours"),
                ("Horario", "schedule"),
                ("Ubicación", "location"),
                ("Inicio", "start_date"),
                ("Fin", "end_date"),
                ("ID profesor", "id_professor|professor.id_professor"),
                ("Profesor", "professor.name"),
                ("Inscritos", "students|enrolled_students"),
            ],
            entity_label="Curso",
            parent=parent,
        )
