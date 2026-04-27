from ca_program.views.admin_base_manager_gui import AdminCrudWidget, FieldSpec


class StudentManagerWidget(AdminCrudWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Gestión de estudiantes",
            description="Registro y consulta de estudiantes según HU-01 y HU-02.",
            service_module="ca_program.services.student_service",
            service_class="StudentService",
            create_method_names=["register_student", "create_student", "add_student", "save_student", "register"],
            list_method_names=["get_students", "list_students", "get_all_students", "consult_students", "get_all"],
            fields=[
                FieldSpec("id_student", "Identificación", "Documento o código del estudiante"),
                FieldSpec("name", "Nombre", "Nombre completo"),
                FieldSpec("password", "Contraseña inicial", "Contraseña temporal", "password"),
                FieldSpec("email", "Correo", "correo@ejemplo.com"),
                FieldSpec("birth_date", "Fecha nacimiento", field_type="date"),
                FieldSpec("nationality", "Nacionalidad", "País de origen"),
            ],
            table_columns=[
                ("Identificación", "id_student"),
                ("Nombre", "name|user.name"),
                ("Correo", "email|user.email"),
                ("Fecha nacimiento", "birth_date|user.birth_date"),
                ("Nacionalidad", "nationality|user.nationality"),
            ],
            entity_label="Estudiante",
            parent=parent,
        )
