from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    placeholder: str = ""
    field_type: str = "text"
    required: bool = True
    minimum: float | int | None = None
    maximum: float | int | None = None
    default: Any = None


class ServiceUnavailable(Exception):
    pass


class AdminCrudWidget(QWidget):
    def __init__(
        self,
        title: str,
        description: str,
        service_module: str,
        service_class: str,
        create_method_names: list[str],
        list_method_names: list[str],
        fields: list[FieldSpec],
        table_columns: list[tuple[str, str]],
        entity_label: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.service_module = service_module
        self.service_class = service_class
        self.create_method_names = create_method_names
        self.list_method_names = list_method_names
        self.fields = fields
        self.table_columns = table_columns
        self.entity_label = entity_label
        self.inputs: dict[str, QWidget] = {}
        self.service_status = QLabel()
        self.search_input = QLineEdit()
        self.table = QTableWidget()
        self.rows: list[Any] = []
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 24, 28, 24)
        root_layout.setSpacing(18)

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
        card.setMinimumWidth(360)
        card.setMaximumWidth(440)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(f"Registrar {self.entity_label.lower()}")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        for row, field in enumerate(self.fields):
            label = QLabel(field.label)
            label.setObjectName("fieldLabel")
            editor = self._make_input(field)
            self.inputs[field.key] = editor
            grid.addWidget(label, row, 0)
            grid.addWidget(editor, row, 1)

        layout.addLayout(grid)
        layout.addStretch()

        save_btn = QPushButton("Guardar registro")
        save_btn.clicked.connect(self.save_record)
        layout.addWidget(save_btn)

        clear_btn = QPushButton("Limpiar formulario")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self.clear_form)
        layout.addWidget(clear_btn)

        return card

    def _create_table_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel(f"{self.entity_label}s registrados")
        title.setObjectName("cardTitle")
        self.search_input.setPlaceholderText(f"Buscar {self.entity_label.lower()} por nombre")
        self.search_input.textChanged.connect(self.apply_filter)
        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(self.search_input, 1)
        layout.addLayout(toolbar)

        self.table.setColumnCount(len(self.table_columns))
        self.table.setHorizontalHeaderLabels([header for header, _ in self.table_columns])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        return card

    def _make_input(self, field: FieldSpec) -> QWidget:
        if field.field_type == "textarea":
            editor = QTextEdit()
            editor.setPlaceholderText(field.placeholder)
            editor.setFixedHeight(80)
            return editor

        if field.field_type == "date":
            editor = QDateEdit()
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
            if field.default:
                editor.setDate(QDate.fromString(str(field.default), "yyyy-MM-dd"))
            else:
                editor.setDate(QDate.currentDate())
            return editor

        if field.field_type == "int":
            editor = QSpinBox()
            editor.setMinimum(int(field.minimum if field.minimum is not None else 0))
            editor.setMaximum(int(field.maximum if field.maximum is not None else 1000000))
            editor.setValue(int(field.default if field.default is not None else editor.minimum()))
            return editor

        if field.field_type == "float":
            editor = QDoubleSpinBox()
            editor.setMinimum(float(field.minimum if field.minimum is not None else 0))
            editor.setMaximum(float(field.maximum if field.maximum is not None else 1000000))
            editor.setDecimals(2)
            editor.setValue(float(field.default if field.default is not None else editor.minimum()))
            return editor

        editor = QLineEdit()
        editor.setPlaceholderText(field.placeholder)
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

    def _collect_payload(self) -> dict[str, Any] | None:
        payload: dict[str, Any] = {}
        missing: list[str] = []
        for field in self.fields:
            value = self._read_input_value(field)
            payload[field.key] = value
            if field.required and (value is None or value == ""):
                missing.append(field.label)
        if missing:
            QMessageBox.warning(self, "Campos obligatorios", "Completa: " + ", ".join(missing))
            return None
        return payload

    def _load_service_target(self) -> Any:
        try:
            module = import_module(self.service_module)
        except Exception as exc:
            raise ServiceUnavailable(
                f"No se encontró {self.service_module}. La vista ya está lista; falta conectar el servicio correspondiente."
            ) from exc

        target = getattr(module, self.service_class, None)
        if target is None:
            raise ServiceUnavailable(
                f"No se encontró la clase {self.service_class} en {self.service_module}."
            )
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
            raise ServiceUnavailable(
                f"{self.service_class} no expone ninguno de estos métodos: {', '.join(method_names)}."
            )

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
                raise RuntimeError(result.get("message", "No fue posible consultar los datos."))
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

    def _validate_action_result(self, result: Any):
        if isinstance(result, dict) and result.get("success") is False:
            raise RuntimeError(result.get("message", "No fue posible guardar el registro."))

    def save_record(self):
        payload = self._collect_payload()
        if payload is None:
            return
        try:
            result = self._call_service(self.create_method_names, payload)
            self._validate_action_result(result)
            QMessageBox.information(self, "Registro guardado", f"{self.entity_label} registrado correctamente.")
            self.clear_form()
            self.refresh_data()
        except ServiceUnavailable as exc:
            QMessageBox.warning(self, "Servicio no disponible", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def refresh_data(self):
        try:
            result = self._call_service(self.list_method_names)
            self.rows = self._extract_rows(result)
            self.service_status.setText(f"Datos actualizados: {len(self.rows)} registro(s).")
            self.service_status.setProperty("state", "ok")
        except ServiceUnavailable as exc:
            self.rows = []
            self.service_status.setText(str(exc))
            self.service_status.setProperty("state", "warning")
        except Exception as exc:
            self.rows = []
            self.service_status.setText(f"No fue posible cargar los datos: {exc}")
            self.service_status.setProperty("state", "warning")
        self.service_status.style().unpolish(self.service_status)
        self.service_status.style().polish(self.service_status)
        self.apply_filter()

    def apply_filter(self):
        text = self.search_input.text().strip().lower()
        filtered = []
        for row in self.rows:
            name = str(self._get_value(row, "name") or self._get_value(row, "user.name") or "").lower()
            if not text or text in name:
                filtered.append(row)
        self._fill_table(filtered)

    def _fill_table(self, rows: list[Any]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, (_, path) in enumerate(self.table_columns):
                value = self._get_value(row, path)
                item = QTableWidgetItem("" if value is None else str(value))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

    def _get_value(self, row: Any, path: str) -> Any:
        if "|" in path:
            for option in path.split("|"):
                value = self._get_value(row, option.strip())
                if value not in (None, ""):
                    return value
            return None

        if isinstance(row, dict):
            current: Any = row
            for part in path.split("."):
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = getattr(current, part, None)
                if current is None:
                    return None
            return current

        if isinstance(row, (list, tuple)):
            keys = [field.key for field in self.fields]
            if path in keys:
                index = keys.index(path)
                if index < len(row):
                    return row[index]
            return None

        current = row
        for part in path.split("."):
            current = getattr(current, part, None)
            if current is None:
                return None
        return current

    def clear_form(self):
        for field in self.fields:
            editor = self.inputs[field.key]
            if isinstance(editor, QLineEdit):
                editor.setText(str(field.default or ""))
            elif isinstance(editor, QTextEdit):
                editor.clear()
            elif isinstance(editor, QDateEdit):
                editor.setDate(QDate.currentDate())
            elif isinstance(editor, QSpinBox):
                editor.setValue(int(field.default if field.default is not None else editor.minimum()))
            elif isinstance(editor, QDoubleSpinBox):
                editor.setValue(float(field.default if field.default is not None else editor.minimum()))
