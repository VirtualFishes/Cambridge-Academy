from ca_program.views.admin_base_manager_gui import AdminCrudWidget, FieldSpec


class ProfessorManagerWidget(AdminCrudWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Gestión de profesores",
            description="Registra y consulta la información del equipo docente de Cambridge Academy.",
            service_module="ca_program.services.professor_service",
            service_class="ProfessorService",
            create_method_names=["register_professor", "create_professor", "add_professor", "save_professor", "register"],
            list_method_names=["get_professors", "list_professors", "get_all_professors", "consult_professors", "get_all"],
            record_identity_field="id_professor",
            record_identity_label="Identificación",
            fields=[
                FieldSpec("id_professor", "Identificación", "Documento o código del profesor"),
                FieldSpec("name", "Nombre", "Nombre completo"),
                FieldSpec("password", "Contraseña", "Contraseña inicial", "password"),
                FieldSpec("email", "Correo", "correo@ejemplo.com"),
                FieldSpec("birth_date", "Fecha de nacimiento", field_type="date"),
                FieldSpec("nationality", "Nacionalidad", "País de origen"),
                FieldSpec("professional_title", "Título profesional", "Título o especialidad"),
            ],
            table_columns=[
                ("Identificación", "id_professor", 145),
                ("Nombre", "name|user.name", 200),
                ("Correo", "email|user.email", 230),
                ("Fecha de\nnacimiento", "birth_date|user.birth_date", 150),
                ("Nacionalidad", "nationality|user.nationality", 150),
                ("Título\nprofesional", "professional_title|title", 210),
            ],
            entity_label="Profesor",
            parent=parent,
        )
