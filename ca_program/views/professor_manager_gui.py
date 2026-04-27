from ca_program.views.admin_base_manager_gui import AdminCrudWidget, FieldSpec


class ProfessorManagerWidget(AdminCrudWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Gestión de profesores",
            description="Registro y consulta de profesores según HU-11 y HU-12.",
            service_module="ca_program.services.professor_service",
            service_class="ProfessorService",
            create_method_names=["register_professor", "create_professor", "add_professor", "save_professor", "register"],
            list_method_names=["get_professors", "list_professors", "get_all_professors", "consult_professors", "get_all"],
            fields=[
                FieldSpec("id_professor", "Identificación", "Documento o código del profesor"),
                FieldSpec("name", "Nombre", "Nombre completo"),
                FieldSpec("password", "Contraseña inicial", "Contraseña temporal", "password"),
                FieldSpec("email", "Correo", "correo@ejemplo.com"),
                FieldSpec("birth_date", "Fecha nacimiento", field_type="date"),
                FieldSpec("nationality", "Nacionalidad", "País de origen"),
                FieldSpec("professional_title", "Título profesional", "Título o especialidad"),
            ],
            table_columns=[
                ("Identificación", "id_professor"),
                ("Nombre", "name|user.name"),
                ("Correo", "email|user.email"),
                ("Fecha nacimiento", "birth_date|user.birth_date"),
                ("Nacionalidad", "nationality|user.nationality"),
                ("Título profesional", "professional_title|title"),
            ],
            entity_label="Profesor",
            parent=parent,
        )
