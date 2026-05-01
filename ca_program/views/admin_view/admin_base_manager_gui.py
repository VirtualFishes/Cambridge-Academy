"""Componentes base reutilizables para la gestión administrativa.

Define un widget CRUD genérico usado por las pantallas de estudiantes,
profesores y cursos. La clase se limita a construir formularios, leer entradas,
invocar servicios y pintar resultados; no ejecuta SQL ni contiene reglas de
negocio propias del dominio.
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from ca_program.views.admin_view.admin_view_utils import build_search_blob, get_nested_value, make_table_item

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class FieldSpec:
    """Describe un campo editable del formulario CRUD administrativo."""
    key: str
    label: str
    placeholder: str = ""
    field_type: str = "text"
    required: bool = True
    minimum: float | int | None = None
    maximum: float | int | None = None
    default: Any = None


TableColumnSpec = tuple[str, str] | tuple[str, str, int]


class ServiceUnavailable(Exception):
    """Señala que el servicio requerido por la vista no pudo cargarse."""

    pass


class AdminCrudWidget(QWidget):
    """Widget CRUD reutilizable para pantallas administrativas simples.

    La clase abstrae formulario, tabla, búsqueda e integración con servicios.
    La configuración se recibe por constructor para evitar duplicar código entre
    estudiantes, profesores y cursos.
    """

    def __init__(
        self,
        title: str,
        description: str,
        service_module: str,
        service_class: str,
        create_method_names: list[str],
        list_method_names: list[str],
        fields: list[FieldSpec],
        table_columns: list[TableColumnSpec],
        entity_label: str,
        update_method_names: list[str] | None = None,
        record_identity_field: str | None = None,
        record_identity_label: str | None = None,
        current_record_payload_key: str | None = None,
        update_optional_fields: list[str] | None = None,
        delete_method_names: list[str] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.service_module = service_module
        self.service_class = service_class
        self.create_method_names = create_method_names
        self.list_method_names = list_method_names
        self.update_method_names = update_method_names or []
        self.delete_method_names = delete_method_names or []
        self.fields = fields
        self.table_columns = table_columns
        self.entity_label = entity_label
        self.record_identity_field = record_identity_field or (fields[0].key if fields else None)
        self.record_identity_label = record_identity_label or self._infer_record_identity_label()
        self.current_record_payload_key = current_record_payload_key or (
            f"current_{self.record_identity_field}" if self.record_identity_field else None
        )
        self.update_optional_fields = set(update_optional_fields or [])

        self.inputs: dict[str, QWidget] = {}
        self.service_status = QLabel()
        self.search_input = QLineEdit()
        self.table = QTableWidget()
        self.rows: list[Any] = []
        self.filtered_rows: list[Any] = []

        self.form_title_label: QLabel | None = None
        self.selection_status_label: QLabel | None = None
        self.save_btn: QPushButton | None = None
        self.clear_btn: QPushButton | None = None
        self.delete_btn: QPushButton | None = None
        self.selected_record: Any | None = None
        self.selected_record_identity: Any | None = None
        self._populating_table = False
        self._loading_form = False

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 24, 28, 24)
        root_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        title_label = QLabel(self.title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(self.description)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)

        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self.refresh_data)

        header_layout.addLayout(header_text_layout, 1)
        header_layout.addWidget(refresh_btn)
        root_layout.addLayout(header_layout)

        self.service_status.setObjectName("serviceStatus")
        self.service_status.setWordWrap(True)
        root_layout.addWidget(self.service_status)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        root_layout.addLayout(content_layout, 1)

        form_card = self._create_form_card()
        table_card = self._create_table_card()

        content_layout.addWidget(form_card, 0)
        content_layout.addWidget(table_card, 1)

    def _create_form_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(410)
        card.setMaximumWidth(455)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.form_title_label = QLabel(f"Registrar {self.entity_label.lower()}")
        self.form_title_label.setObjectName("cardTitle")
        layout.addWidget(self.form_title_label)

        if self._supports_row_selection():
            self.selection_status_label = QLabel(self._initial_selection_text())
            self.selection_status_label.setObjectName("selectionStatus")
            self.selection_status_label.setWordWrap(True)
            self.selection_status_label.setFixedHeight(44)
            layout.addWidget(self.selection_status_label)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("formScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(280)

        scroll_content = QWidget()
        scroll_content.setObjectName("formScrollContent")
        fields_layout = QVBoxLayout(scroll_content)
        fields_layout.setContentsMargins(0, 0, 8, 0)
        fields_layout.setSpacing(12)

        for field in self.fields:
            field_box = QWidget()
            field_box.setObjectName("fieldBox")
            field_layout = QVBoxLayout(field_box)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(5)

            label = QLabel(field.label)
            label.setObjectName("fieldLabel")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setWordWrap(True)

            editor = self._make_input(field)
            self.inputs[field.key] = editor

            field_layout.addWidget(label)
            field_layout.addWidget(editor)
            fields_layout.addWidget(field_box)

        fields_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)

        self.save_btn = QPushButton("Guardar registro")
        self.save_btn.clicked.connect(self._handle_primary_action)
        self.save_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.save_btn)

        secondary_actions_layout = QHBoxLayout()
        secondary_actions_layout.setContentsMargins(0, 0, 0, 0)
        secondary_actions_layout.setSpacing(10)

        self.clear_btn = QPushButton("Limpiar formulario")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self._handle_secondary_action)
        self.clear_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        secondary_actions_layout.addWidget(self.clear_btn, 1)

        if self._supports_delete():
            self.delete_btn = QPushButton(f"Eliminar {self.entity_label.lower()}")
            self.delete_btn.setObjectName("dangerButton")
            self.delete_btn.setVisible(False)
            self.delete_btn.clicked.connect(self.delete_record)
            self.delete_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.delete_btn.setStyleSheet('''
                QPushButton#dangerButton {
                    background-color: #fff1f2;
                    color: #991b1b;
                    border: 1px solid #fecdd3;
                    border-radius: 10px;
                    padding: 9px 12px;
                    font-weight: 700;
                }
                QPushButton#dangerButton:hover {
                    background-color: #fee2e2;
                    border: 1px solid #fca5a5;
                }
                QPushButton#dangerButton:pressed {
                    background-color: #fecaca;
                }
            ''')
            secondary_actions_layout.addWidget(self.delete_btn, 1)

        layout.addLayout(secondary_actions_layout)
        return card

    def _create_table_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        title = QLabel(f"{self._plural_label()} registrados")
        title.setObjectName("cardTitle")
        self.search_input.setPlaceholderText(f"Buscar {self.entity_label.lower()} por nombre")
        self.search_input.setMinimumWidth(260)
        self.search_input.textChanged.connect(self.apply_filter)
        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(self.search_input, 1)
        layout.addLayout(toolbar)

        self.table.setColumnCount(len(self.table_columns))
        self.table.setHorizontalHeaderLabels([self._column_header(column) for column in self.table_columns])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)

        if self._supports_row_selection():
            self.table.itemSelectionChanged.connect(self._handle_table_selection)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setMinimumSectionSize(90)
        header.setDefaultSectionSize(135)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setFixedHeight(48)

        self._apply_column_widths()
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        return card

    def _make_input(self, field: FieldSpec) -> QWidget:
        if field.field_type == "textarea":
            editor = QTextEdit()
            editor.setPlaceholderText(field.placeholder)
            editor.setFixedHeight(70)
            editor.setTabChangesFocus(True)
            editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return editor

        if field.field_type == "date":
            editor = QDateEdit()
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
            if field.default:
                editor.setDate(QDate.fromString(str(field.default), "yyyy-MM-dd"))
            else:
                editor.setDate(QDate.currentDate())
            editor.setMinimumHeight(38)
            editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return editor

        if field.field_type == "int":
            editor = QSpinBox()
            editor.setMinimum(int(field.minimum if field.minimum is not None else 0))
            editor.setMaximum(int(field.maximum if field.maximum is not None else 1000000))
            editor.setValue(int(field.default if field.default is not None else editor.minimum()))
            editor.setButtonSymbols(QAbstractSpinBox.NoButtons)
            editor.setMinimumHeight(38)
            editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return editor

        if field.field_type == "float":
            editor = QDoubleSpinBox()
            editor.setMinimum(float(field.minimum if field.minimum is not None else 0))
            editor.setMaximum(float(field.maximum if field.maximum is not None else 1000000))
            editor.setDecimals(2)
            editor.setValue(float(field.default if field.default is not None else editor.minimum()))
            editor.setButtonSymbols(QAbstractSpinBox.NoButtons)
            editor.setMinimumHeight(38)
            editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return editor

        editor = QLineEdit()
        editor.setPlaceholderText(field.placeholder)
        editor.setMinimumHeight(38)
        editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if field.default is not None:
            editor.setText(str(field.default))
        if field.field_type == "password":
            editor.setEchoMode(QLineEdit.Password)
        return editor

    def _read_input_value(self, field: FieldSpec) -> Any:
        editor = self.inputs[field.key]
        if isinstance(editor, QTextEdit):
            return editor.toPlainText().strip()
        if isinstance(editor, QLineEdit):
            return editor.text().strip()
        if isinstance(editor, QDateEdit):
            return editor.date().toString("yyyy-MM-dd")
        if isinstance(editor, QSpinBox):
            return editor.value()
        if isinstance(editor, QDoubleSpinBox):
            return float(editor.value())
        return None

    def _set_input_value(self, field: FieldSpec, value: Any):
        editor = self.inputs[field.key]

        if isinstance(editor, QTextEdit):
            editor.setPlainText("" if value is None else str(value))
            return

        if isinstance(editor, QLineEdit):
            editor.setText("" if value is None else str(value))
            return

        if isinstance(editor, QDateEdit):
            parsed_date = QDate.fromString(str(value), "yyyy-MM-dd") if value is not None else QDate()
            editor.setDate(parsed_date if parsed_date.isValid() else QDate.currentDate())
            return

        if isinstance(editor, QSpinBox):
            editor.setValue(int(value if value is not None else editor.minimum()))
            return

        if isinstance(editor, QDoubleSpinBox):
            editor.setValue(float(value if value is not None else editor.minimum()))
            return

    def _collect_payload(self, for_update: bool = False) -> dict[str, Any] | None:
        payload: dict[str, Any] = {}
        missing: list[str] = []
        for field in self.fields:
            value = self._read_input_value(field)
            payload[field.key] = value
            is_optional_for_update = for_update and field.key in self.update_optional_fields
            if field.required and not is_optional_for_update and (value is None or value == ""):
                missing.append(field.label)
        if missing:
            QMessageBox.warning(self, "Campos obligatorios", "Completa: " + ", ".join(missing))
            return None
        return payload

    def _load_service_target(self) -> Any:
        try:
            module = import_module(self.service_module)
        except Exception as exc:
            print(f"No se pudo cargar el servicio {self.service_module}: {exc}")
            raise ServiceUnavailable(self._unavailable_message()) from exc

        target = getattr(module, self.service_class, None)
        if target is None:
            print(f"No se encontró el componente {self.service_class} en {self.service_module}.")
            raise ServiceUnavailable(self._unavailable_message())
        return target

    def _call_service(self, method_names: list[str], payload: dict[str, Any] | None = None) -> Any:
        target = self._load_service_target()
        method: Callable[..., Any] | None = None
        for name in method_names:
            candidate = getattr(target, name, None)
            if callable(candidate):
                method = candidate
                break

        if method is None:
            print(f"No se encontró una acción disponible para {self.service_class}: {method_names}")
            raise ServiceUnavailable(self._unavailable_message())

        if payload is None:
            return method()
        try:
            return method(payload)
        except TypeError:
            return method(**payload)

    def _extract_rows(self, result: Any) -> list[Any]:
        if result is None:
            return []
        if isinstance(result, dict):
            if result.get("success") is False:
                print(f"No fue posible consultar la información: {result.get('message')}")
                raise RuntimeError("No fue posible consultar la información. Intenta nuevamente.")
            for key in ("data", "records", "items", "students", "courses", "professors", "result"):
                value = result.get(key)
                if isinstance(value, list):
                    return value
            return []
        if isinstance(result, list):
            return result
        if isinstance(result, tuple):
            return list(result)
        return []

    def _validate_action_result(self, result: Any, action_name: str = "guardar"):
        if isinstance(result, dict) and result.get("success") is False:
            print(f"No fue posible {action_name} el registro: {result.get('message')}")
            user_message = result.get("message") or "Verifica los datos e intenta nuevamente."
            raise RuntimeError(user_message)

    def _handle_primary_action(self):
        if self._supports_update() and self.selected_record is not None:
            self.update_record()
            return

        self.save_record()

    def _handle_secondary_action(self):
        self.clear_form()

    def save_record(self):
        payload = self._collect_payload(for_update=False)
        if payload is None:
            return
        try:
            result = self._call_service(self.create_method_names, payload)
            self._validate_action_result(result, "guardar")
            QMessageBox.information(self, "Registro guardado", f"{self.entity_label} registrado correctamente.")
            self.clear_form()
            self.refresh_data()
        except ServiceUnavailable as exc:
            QMessageBox.warning(self, "Información no disponible", str(exc))
        except RuntimeError as exc:
            QMessageBox.warning(self, "No fue posible guardar", str(exc))
        except Exception as exc:
            print(f"Error inesperado al guardar {self.entity_label}: {exc}")
            QMessageBox.critical(
                self,
                "No fue posible guardar",
                "Ocurrió un inconveniente al guardar el registro. Intenta nuevamente.",
            )

    def update_record(self):
        if not self._supports_update():
            return

        if self.selected_record is None or self.selected_record_identity in (None, ""):
            QMessageBox.information(
                self,
                "Selecciona un registro",
                f"Selecciona un {self.entity_label.lower()} de la tabla antes de modificar.",
            )
            return

        payload = self._collect_payload(for_update=True)
        if payload is None:
            return

        if self.current_record_payload_key:
            payload[self.current_record_payload_key] = self.selected_record_identity

        response = QMessageBox.question(
            self,
            "Confirmar modificación",
            f"¿Deseas guardar los cambios del {self.entity_label.lower()} seleccionado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return

        try:
            result = self._call_service(self.update_method_names, payload)
            self._validate_action_result(result, "modificar")
            QMessageBox.information(self, "Registro actualizado", f"{self.entity_label} modificado correctamente.")
            self.clear_form()
            self.refresh_data()
        except ServiceUnavailable as exc:
            QMessageBox.warning(self, "Información no disponible", str(exc))
        except RuntimeError as exc:
            QMessageBox.warning(self, "No fue posible modificar", str(exc))
        except Exception as exc:
            print(f"Error inesperado al modificar {self.entity_label}: {exc}")
            QMessageBox.critical(
                self,
                "No fue posible modificar",
                "Ocurrió un inconveniente al modificar el registro. Intenta nuevamente.",
            )

    def delete_record(self):
        if not self._supports_delete():
            return

        if self.selected_record is None or self.selected_record_identity in (None, ""):
            QMessageBox.information(
                self,
                "Selecciona un registro",
                f"Selecciona un {self.entity_label.lower()} de la tabla antes de eliminar.",
            )
            return

        record_name = (
            self._get_field_value_for_form(self.selected_record, "name")
            or self._get_field_value_for_form(self.selected_record, "title")
            or self._get_field_value_for_form(self.selected_record, "course_name")
            or "registro seleccionado"
        )

        confirmation_text = (
            f"¿Eliminar {self.entity_label.lower()}?\n\n"
            f"Se eliminará permanentemente este registro:\n"
            f"{record_name}\n"
            f"{self.record_identity_label}: {self.selected_record_identity}\n\n"
            "Esta acción no se puede deshacer."
        )

        response = QMessageBox.warning(
            self,
            f"Eliminar {self.entity_label.lower()}",
            confirmation_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return

        payload: dict[str, Any] = {}
        if self.record_identity_field:
            payload[self.record_identity_field] = self.selected_record_identity
        if self.current_record_payload_key:
            payload[self.current_record_payload_key] = self.selected_record_identity

        try:
            result = self._call_service(self.delete_method_names, payload)
            self._validate_action_result(result, "eliminar")
            QMessageBox.information(self, "Registro eliminado", f"{self.entity_label} eliminado correctamente.")
            self.clear_form()
            self.refresh_data()
        except ServiceUnavailable as exc:
            QMessageBox.warning(self, "Información no disponible", str(exc))
        except RuntimeError as exc:
            QMessageBox.warning(self, "No fue posible eliminar", str(exc))
        except Exception as exc:
            print(f"Error inesperado al eliminar {self.entity_label}: {exc}")
            QMessageBox.critical(
                self,
                "No fue posible eliminar",
                "Ocurrió un inconveniente al eliminar el registro. Intenta nuevamente.",
            )

    def refresh_data(self):
        try:
            result = self._call_service(self.list_method_names)
            self.rows = self._extract_rows(result)
            self.service_status.setText(f"Información actualizada: {len(self.rows)} registro(s).")
            self.service_status.setProperty("state", "ok")
        except ServiceUnavailable as exc:
            self.rows = []
            self.service_status.setText(str(exc))
            self.service_status.setProperty("state", "warning")
        except Exception as exc:
            print(f"Error inesperado al cargar {self._plural_label().lower()}: {exc}")
            self.rows = []
            self.service_status.setText("No fue posible cargar la información. Intenta actualizar de nuevo.")
            self.service_status.setProperty("state", "warning")
        self.service_status.style().unpolish(self.service_status)
        self.service_status.style().polish(self.service_status)
        self.apply_filter()

    def apply_filter(self):
        """Filtra la tabla usando las columnas visibles y campos del formulario."""
        text = self.search_input.text().strip().lower()
        searchable_paths = [self._column_path(column) for column in self.table_columns]
        searchable_paths.extend(field.key for field in self.fields)

        filtered = []
        for row in self.rows:
            search_blob = build_search_blob(row, searchable_paths)
            if not text or text in search_blob:
                filtered.append(row)

        self.filtered_rows = filtered
        self._fill_table(filtered)

    def _fill_table(self, rows: list[Any]):
        self._populating_table = True
        if self._supports_row_selection():
            self._set_edit_state(None)
        self.table.setSortingEnabled(False)
        self.table.clearSelection()
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, column in enumerate(self.table_columns):
                value = self._get_value(row, self._column_path(column))
                item = make_table_item(value, Qt.AlignVCenter | Qt.AlignLeft)
                item.setData(Qt.UserRole, row)
                self.table.setItem(row_index, col_index, item)
        self._apply_column_widths()
        self.table.setSortingEnabled(True)
        self._populating_table = False

    def _handle_table_selection(self):
        if self._populating_table or self._loading_form:
            return

        selected_items = self.table.selectedItems()
        if not selected_items:
            self._set_edit_state(None)
            return

        selected_row = selected_items[0].row()
        first_item = self.table.item(selected_row, 0)
        row_data = first_item.data(Qt.UserRole) if first_item is not None else None
        if row_data is None:
            return

        self._load_record_into_form(row_data)

    def _load_record_into_form(self, row: Any):
        self._loading_form = True
        try:
            for field in self.fields:
                if field.field_type == "password":
                    self._set_input_value(field, "")
                    editor = self.inputs.get(field.key)
                    if isinstance(editor, QLineEdit):
                        editor.setPlaceholderText("Dejar vacío para conservar la contraseña actual")
                    continue

                value = self._get_field_value_for_form(row, field.key)
                self._set_input_value(field, value)
        finally:
            self._loading_form = False

        self._set_edit_state(row)

    def _set_edit_state(self, row: Any | None):
        self.selected_record = row
        self.selected_record_identity = None

        if row is not None and self.record_identity_field:
            self.selected_record_identity = self._get_field_value_for_form(row, self.record_identity_field)

        if self.form_title_label is not None:
            if row is None:
                self.form_title_label.setText(f"Registrar {self.entity_label.lower()}")
            else:
                self.form_title_label.setText(f"Editar {self.entity_label.lower()}")

        if self.selection_status_label is not None:
            if row is None:
                self.selection_status_label.setText(self._initial_selection_text())
                self.selection_status_label.setProperty("state", "info")
            else:
                self.selection_status_label.setText(self._selected_selection_text())
                self.selection_status_label.setProperty("state", "selected")
            self.selection_status_label.style().unpolish(self.selection_status_label)
            self.selection_status_label.style().polish(self.selection_status_label)

        if self.save_btn is not None:
            self.save_btn.setText("Guardar registro" if row is None else "Guardar cambios")

        if self.clear_btn is not None:
            self.clear_btn.setText("Limpiar formulario" if row is None else "Cancelar edición")

        if self.delete_btn is not None:
            self.delete_btn.setVisible(row is not None and self._supports_delete())

    def _get_field_value_for_form(self, row: Any, field_key: str) -> Any:
        value = self._get_value(row, field_key)
        if value not in (None, ""):
            return value
        return self._get_value(row, f"user.{field_key}")

    def _get_value(self, row: Any, path: str) -> Any:
        """Lee un valor desde dicts, objetos o tuplas usadas por servicios legacy."""
        if isinstance(row, (list, tuple)):
            keys = [field.key for field in self.fields]
            if path in keys:
                index = keys.index(path)
                if index < len(row):
                    return row[index]
            return None

        return get_nested_value(row, path)

    def clear_form(self):
        self._loading_form = True
        try:
            for field in self.fields:
                editor = self.inputs[field.key]
                if isinstance(editor, QLineEdit):
                    editor.setText(str(field.default or ""))
                    editor.setPlaceholderText(field.placeholder)
                elif isinstance(editor, QTextEdit):
                    editor.clear()
                elif isinstance(editor, QDateEdit):
                    if field.default:
                        editor.setDate(QDate.fromString(str(field.default), "yyyy-MM-dd"))
                    else:
                        editor.setDate(QDate.currentDate())
                elif isinstance(editor, QSpinBox):
                    editor.setValue(int(field.default if field.default is not None else editor.minimum()))
                elif isinstance(editor, QDoubleSpinBox):
                    editor.setValue(float(field.default if field.default is not None else editor.minimum()))
        finally:
            self._loading_form = False

        if self._supports_row_selection():
            self.table.clearSelection()
            self._set_edit_state(None)

    def _supports_update(self) -> bool:
        return bool(self.update_method_names)

    def _supports_delete(self) -> bool:
        return bool(self.delete_method_names)

    def _supports_row_selection(self) -> bool:
        return self._supports_update() or self._supports_delete()

    def _column_header(self, column: TableColumnSpec) -> str:
        return column[0]

    def _column_path(self, column: TableColumnSpec) -> str:
        return column[1]

    def _column_width(self, column: TableColumnSpec) -> int:
        if len(column) >= 3:
            return int(column[2])
        return 135

    def _apply_column_widths(self):
        for index, column in enumerate(self.table_columns):
            self.table.setColumnWidth(index, self._column_width(column))

    def _plural_label(self) -> str:
        lower_label = self.entity_label.lower()
        if lower_label == "curso":
            return "Cursos"
        if lower_label == "profesor":
            return "Profesores"
        if lower_label == "estudiante":
            return "Estudiantes"
        return f"{self.entity_label}s"

    def _initial_selection_text(self) -> str:
        if self._supports_update() and self._supports_delete():
            return "Selecciona un registro de la tabla para modificarlo o eliminarlo."
        if self._supports_update():
            return "Selecciona un registro de la tabla para modificarlo."
        if self._supports_delete():
            return "Selecciona un registro de la tabla para eliminarlo."
        return "Selecciona un registro de la tabla."

    def _selected_selection_text(self) -> str:
        parts: list[str] = []

        if self._supports_update():
            parts.append("Editar | Guardar | ")

        if self._supports_delete():
            parts.append("Eliminar | ")

        if self._has_password_field():
            parts.append("Cambiar contraseña ")

        return " ".join(parts) if parts else "Registro seleccionado."

    def _has_password_field(self) -> bool:
        return any(field.field_type == "password" for field in self.fields)

    def _infer_record_identity_label(self) -> str:
        if not self.record_identity_field:
            return "Identificador"

        for field in self.fields:
            if field.key == self.record_identity_field:
                return field.label

        friendly_labels = {
            "code_course": "Código",
            "id_student": "Identificación",
            "id_professor": "Identificación",
            "id_user": "Identificación",
        }
        return friendly_labels.get(self.record_identity_field, "Identificador")

    def _unavailable_message(self) -> str:
        return (
            "La información no está disponible en este momento. "
            "Verifica la conexión o intenta actualizar nuevamente."
        )
