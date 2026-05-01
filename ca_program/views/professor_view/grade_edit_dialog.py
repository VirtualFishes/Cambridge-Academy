from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ca_program.services.grade_service import GradeService


class GradeEditDialog(QDialog):
    """Diálogo para corregir notas registradas.

    Esta ventana corresponde a la HU-28. Solo captura los nuevos valores de
    Nota 1, Nota 2 y Nota 3; la actualización real, validación de permisos y
    persistencia deben ejecutarse desde GradeService.
    """

    def __init__(self, grade_record: dict | None = None, parent=None):
        super().__init__(parent)
        self.grade_record = grade_record or {}

        self.setWindowTitle("Editar notas")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setObjectName("gradeEditDialog")
        self.setStyleSheet(self.get_styles())

        self._build_ui()
        self.set_grade_record(self.grade_record)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("gradeEditHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.title_label = QLabel("Editar notas")
        self.title_label.setObjectName("gradeEditTitle")
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel("Corrige las notas registradas del estudiante seleccionado.")
        self.subtitle_label.setObjectName("gradeEditSubtitle")
        self.subtitle_label.setWordWrap(True)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)

        self.student_card = QFrame()
        self.student_card.setObjectName("gradeEditStudentCard")
        student_layout = QGridLayout(self.student_card)
        student_layout.setContentsMargins(16, 14, 16, 14)
        student_layout.setHorizontalSpacing(16)
        student_layout.setVerticalSpacing(8)

        self.student_name_label = self._create_value_label("Estudiante sin nombre")
        self.enrollment_label = self._create_value_label("No registrada")
        self.email_label = self._create_value_label("No registrado")

        student_layout.addWidget(self._create_caption_label("ESTUDIANTE"), 0, 0)
        student_layout.addWidget(self._create_caption_label("MATRÍCULA"), 0, 1)
        student_layout.addWidget(self._create_caption_label("CORREO"), 2, 0, 1, 2)
        student_layout.addWidget(self.student_name_label, 1, 0)
        student_layout.addWidget(self.enrollment_label, 1, 1)
        student_layout.addWidget(self.email_label, 3, 0, 1, 2)
        student_layout.setColumnStretch(0, 2)
        student_layout.setColumnStretch(1, 1)

        self.form_card = QFrame()
        self.form_card.setObjectName("gradeEditFormCard")
        form_layout = QGridLayout(self.form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setHorizontalSpacing(14)
        form_layout.setVerticalSpacing(12)

        self.grade1_input = self._create_grade_spinbox()
        self.grade2_input = self._create_grade_spinbox()
        self.grade3_input = self._create_grade_spinbox()

        self.average_label = QLabel("0.00")
        self.average_label.setObjectName("gradeEditAverageValue")
        self.average_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Sin estado")
        self.status_label.setObjectName("gradeEditStatusValue")
        self.status_label.setAlignment(Qt.AlignCenter)

        form_layout.addWidget(self._create_caption_label("NOTA 1"), 0, 0)
        form_layout.addWidget(self._create_caption_label("NOTA 2"), 0, 1)
        form_layout.addWidget(self._create_caption_label("NOTA 3"), 0, 2)
        form_layout.addWidget(self.grade1_input, 1, 0)
        form_layout.addWidget(self.grade2_input, 1, 1)
        form_layout.addWidget(self.grade3_input, 1, 2)
        form_layout.addWidget(self._create_caption_label("PROMEDIO"), 2, 0)
        form_layout.addWidget(self._create_caption_label("ESTADO"), 2, 1, 1, 2)
        form_layout.addWidget(self.average_label, 3, 0)
        form_layout.addWidget(self.status_label, 3, 1, 1, 2)

        self.info_label = QLabel(
            "El promedio y el estado se recalculan automáticamente. "
            "La actualización definitiva se valida contra el curso y el profesor autenticado."
        )
        self.info_label.setObjectName("gradeEditInfoLabel")
        self.info_label.setWordWrap(True)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("gradeEditSecondaryButton")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("Guardar cambios")
        self.save_button.setObjectName("gradeEditPrimaryButton")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.accept)

        actions_layout.addStretch()
        actions_layout.addWidget(self.cancel_button)
        actions_layout.addWidget(self.save_button)

        self.grade1_input.valueChanged.connect(self._refresh_calculation)
        self.grade2_input.valueChanged.connect(self._refresh_calculation)
        self.grade3_input.valueChanged.connect(self._refresh_calculation)

        main_layout.addWidget(header)
        main_layout.addWidget(self.student_card)
        main_layout.addWidget(self.form_card)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(actions)

    def set_grade_record(self, grade_record: dict | None):
        self.grade_record = grade_record or {}

        student_name = self._read_value(self.grade_record, "student_name", default="Estudiante sin nombre")
        id_enrollment = self._read_value(self.grade_record, "id_enrollment", default="No registrada")
        student_email = self._read_value(self.grade_record, "student_email", default="No registrado")

        self.student_name_label.setText(student_name)
        self.enrollment_label.setText(str(id_enrollment))
        self.email_label.setText(student_email)
        self.title_label.setText(f"Editar notas — {student_name}")

        self.grade1_input.blockSignals(True)
        self.grade2_input.blockSignals(True)
        self.grade3_input.blockSignals(True)
        self.grade1_input.setValue(self._read_float(self.grade_record, "grade1"))
        self.grade2_input.setValue(self._read_float(self.grade_record, "grade2"))
        self.grade3_input.setValue(self._read_float(self.grade_record, "grade3"))
        self.grade1_input.blockSignals(False)
        self.grade2_input.blockSignals(False)
        self.grade3_input.blockSignals(False)

        self._refresh_calculation()

    def get_values(self) -> dict:
        grade1 = round(float(self.grade1_input.value()), 2)
        grade2 = round(float(self.grade2_input.value()), 2)
        grade3 = round(float(self.grade3_input.value()), 2)
        average = self._calculate_average(grade1, grade2, grade3)

        return {
            "id_grade": self._read_value(self.grade_record, "id_grade", default=""),
            "id_enrollment": self._read_value(self.grade_record, "id_enrollment", default=""),
            "grade1": grade1,
            "grade2": grade2,
            "grade3": grade3,
            "average": average,
            "status_label": self._get_status_from_average(average),
        }

    def get_grade_values(self) -> dict:
        return self.get_values()

    def _refresh_calculation(self):
        average = self._calculate_average(
            self.grade1_input.value(),
            self.grade2_input.value(),
            self.grade3_input.value(),
        )
        status = self._get_status_from_average(average)

        self.average_label.setText(f"{average:.2f}")
        self.status_label.setText(status)
        self.status_label.setProperty("status", "passed" if status == "Aprobado" else "failed")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    @staticmethod
    def _create_grade_spinbox() -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setObjectName("gradeEditSpinBox")
        spinbox.setRange(GradeService.MIN_GRADE, GradeService.MAX_GRADE)
        spinbox.setDecimals(2)
        spinbox.setSingleStep(0.1)
        spinbox.setAlignment(Qt.AlignCenter)
        spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        spinbox.setMinimumWidth(120)
        spinbox.setMinimumHeight(42)
        return spinbox

    @staticmethod
    def _create_caption_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("gradeEditCaption")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_value_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("gradeEditValueText")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _calculate_average(grade1: float, grade2: float, grade3: float) -> float:
        return round((float(grade1) + float(grade2) + float(grade3)) / 3, 2)

    @staticmethod
    def _get_status_from_average(average: float) -> str:
        return "Aprobado" if float(average) >= GradeService.PASSING_GRADE else "Reprobado"

    @staticmethod
    def _read_value(record: dict, key: str, default: str = "") -> str:
        if not isinstance(record, dict):
            return default

        value = record.get(key)
        if value not in (None, ""):
            return str(value).strip()
        return default

    @staticmethod
    def _read_float(record: dict, key: str, default: float = 0.0) -> float:
        if not isinstance(record, dict):
            return default

        value = record.get(key, default)
        if isinstance(value, str):
            value = value.strip().replace(",", ".")

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def get_styles() -> str:
        return """
        QDialog#gradeEditDialog {
            background-color: #eaf0f8;
            color: #1e293b;
            font-size: 14px;
        }

        QFrame#gradeEditHeader {
            background-color: transparent;
            border: none;
        }

        QLabel#gradeEditTitle {
            color: #1e3a8a;
            font-size: 24px;
            font-weight: 900;
        }

        QLabel#gradeEditSubtitle {
            color: #475569;
            font-size: 13px;
            font-weight: 600;
        }

        QFrame#gradeEditStudentCard,
        QFrame#gradeEditFormCard {
            background-color: white;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
        }

        QLabel#gradeEditCaption {
            color: #64748b;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: 0.4px;
        }

        QLabel#gradeEditValueText {
            color: #0f172a;
            font-size: 14px;
            font-weight: 800;
        }

        QDoubleSpinBox#gradeEditSpinBox {
            background-color: white;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 8px 10px;
            font-size: 15px;
            font-weight: 900;
        }

        QDoubleSpinBox#gradeEditSpinBox:focus {
            border-color: #2563eb;
            background-color: #f8fbff;
        }

        QLabel#gradeEditAverageValue {
            background-color: #f8fbff;
            color: #0f172a;
            border: 1px solid #dbeafe;
            border-radius: 10px;
            padding: 10px;
            font-size: 16px;
            font-weight: 900;
        }

        QLabel#gradeEditStatusValue {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            border-radius: 10px;
            padding: 10px;
            font-size: 15px;
            font-weight: 900;
        }

        QLabel#gradeEditStatusValue[status="passed"] {
            background-color: #dcfce7;
            color: #166534;
            border-color: #bbf7d0;
        }

        QLabel#gradeEditStatusValue[status="failed"] {
            background-color: #fee2e2;
            color: #991b1b;
            border-color: #fecaca;
        }

        QLabel#gradeEditInfoLabel {
            background-color: #dbeafe;
            color: #1e40af;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 12px 14px;
            font-weight: 700;
        }

        QPushButton#gradeEditPrimaryButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 11px 18px;
            font-weight: 900;
        }

        QPushButton#gradeEditPrimaryButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton#gradeEditSecondaryButton {
            background-color: white;
            color: #1e3a8a;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 11px 18px;
            font-weight: 800;
        }

        QPushButton#gradeEditSecondaryButton:hover {
            background-color: #eff6ff;
            border-color: #93c5fd;
        }
        """
