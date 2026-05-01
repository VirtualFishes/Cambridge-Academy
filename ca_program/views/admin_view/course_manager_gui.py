"""Vista administrativa para gestión de cursos."""

from ca_program.views.admin_view.admin_base_manager_gui import AdminCrudWidget, FieldSpec


class CourseManagerWidget(AdminCrudWidget):
    """Configura el CRUD administrativo para cursos."""

    def __init__(self, parent=None):
        super().__init__(
            title="Gestión de cursos",
            description="Registra, consulta, actualiza y elimina la información de la oferta académica de Cambridge Academy.",
            service_module="ca_program.services.course_service",
            service_class="CourseService",
            create_method_names=["register_course", "create_course", "add_course", "save_course", "register"],
            list_method_names=["get_courses", "list_courses", "get_all_courses", "consult_courses", "get_all"],
            update_method_names=["update_course", "modify_course", "edit_course", "save_course_changes", "update"],
            delete_method_names=["delete_course", "remove_course", "delete_by_code", "delete_by_id", "delete", "destroy_course"],
            record_identity_field="code_course",
            record_identity_label="Código",
            current_record_payload_key="current_code_course",
            fields=[
                FieldSpec("name", "Nombre", "Nombre del curso"),
                FieldSpec("description", "Descripción", "Resumen breve del curso", "textarea"),
                FieldSpec("price", "Precio", field_type="float", minimum=0, maximum=100000000),
                FieldSpec("duration_days", "Duración (días)", field_type="int", minimum=1, maximum=3650, default=30),
                FieldSpec("intensity_hours", "Intensidad (horas)", field_type="int", minimum=1, maximum=5000, default=40),
                FieldSpec("schedule", "Horario", "Ej: Lunes y miércoles 6:00 p.m."),
                FieldSpec("location", "Ubicación", "Aula, sede o modalidad"),
                FieldSpec("start_date", "Fecha de inicio", field_type="date"),
                FieldSpec("end_date", "Fecha de finalización", field_type="date"),
                FieldSpec("id_professor", "Profesor asignado", "Identificación del profesor"),
            ],
            table_columns=[
                ("Código", "code_course", 95),
                ("Nombre", "name", 180),
                ("Precio", "price", 110),
                ("Duración\n(días)", "duration_days", 125),
                ("Intensidad\n(horas)", "intensity_hours", 135),
                ("Horario", "schedule", 190),
                ("Ubicación", "location", 160),
                ("Fecha de\ninicio", "start_date", 130),
                ("Fecha de\nfinalización", "end_date", 150),
                ("Identificación\nprofesor", "id_professor|professor.id_professor", 155),
                ("Profesor", "professor.name", 170),
                ("Inscritos", "students|enrolled_students", 110),
            ],
            entity_label="Curso",
            parent=parent,
        )
