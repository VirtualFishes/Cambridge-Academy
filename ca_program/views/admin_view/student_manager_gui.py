from ca_program.views.admin_view.admin_base_manager_gui import AdminCrudWidget, FieldSpec


class StudentManagerWidget(AdminCrudWidget):
    def __init__(self, parent=None):
        super().__init__(
            title="Gestión de estudiantes",
            description="Registra, consulta y actualiza la información básica de los estudiantes de Cambridge Academy.",
            service_module="ca_program.services.student_service",
            service_class="StudentService",
            create_method_names=["register_student", "create_student", "add_student", "save_student", "register"],
            list_method_names=["get_students", "list_students", "get_all_students", "consult_students", "get_all"],
            update_method_names=["update_student", "modify_student", "edit_student", "save_student_changes", "update"],
            delete_method_names=["delete_student", "remove_student", "delete_by_id", "delete", "destroy_student"],
            record_identity_field="id_student",
            current_record_payload_key="current_id_student",
            update_optional_fields=["password"],
            fields=[
                FieldSpec("id_student", "Identificación", "Documento o código del estudiante"),
                FieldSpec("name", "Nombre", "Nombre completo"),
                FieldSpec("password", "Contraseña", "Contraseña inicial o nueva contraseña", "password"),
                FieldSpec("email", "Correo", "correo@ejemplo.com"),
                FieldSpec("birth_date", "Fecha de nacimiento", field_type="date"),
                FieldSpec("nationality", "Nacionalidad", "País de origen"),
            ],
            table_columns=[
                ("Identificación", "id_student", 145),
                ("Nombre", "name|user.name", 200),
                ("Correo", "email|user.email", 230),
                ("Fecha de\nnacimiento", "birth_date|user.birth_date", 150),
                ("Nacionalidad", "nationality|user.nationality", 150),
            ],
            entity_label="Estudiante",
            parent=parent,
        )
