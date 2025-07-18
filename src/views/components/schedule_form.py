import logging
from typing import Optional, List
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QLabel, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from ...models.backup_schedule import BackupSchedule
from ...repositories.backup_config_repository import backup_config_repository
from ...utils.validators import is_valid_time_format, is_valid_days_of_week, is_valid_day_of_month
from ...utils.constants import SCHEDULE_TYPES, DAYS_OF_WEEK, SCHEDULE_TYPE_DAILY, SCHEDULE_TYPE_WEEKLY, SCHEDULE_TYPE_MONTHLY
from ...utils.helpers import get_icon
from ...services.notification_service import notification_service

logger = logging.getLogger(__name__)

class ScheduleForm(QDialog):
    schedule_saved = pyqtSignal()

    def __init__(self, parent=None, schedule: Optional[BackupSchedule] = None):
        super().__init__(parent)
        self.schedule_repo = backup_config_repository # Usar config_repo para obtener nombres de config
        self.current_schedule = schedule
        self.setWindowTitle("Editar Programación" if schedule else "Añadir Programación")
        self.setFixedSize(450, 400)
        self._init_ui()
        self.load_configs_for_combo()
        if schedule:
            self._load_schedule_data(schedule)
        logger.info("Formulario de programación inicializado.")

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignRight)

        # Configuración de la base de datos
        self.config_combo = QComboBox()
        self.form_layout.addRow("Configuración DB:", self.config_combo)

        # Tipo de programación
        self.schedule_type_combo = QComboBox()
        self.schedule_type_combo.addItems([s.capitalize() for s in SCHEDULE_TYPES])
        self.schedule_type_combo.currentIndexChanged.connect(self._on_schedule_type_changed)
        self.form_layout.addRow("Tipo de Programación:", self.schedule_type_combo)

        # Hora de ejecución
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("HH:MM (ej. 02:30)")
        self.form_layout.addRow("Hora de Ejecución:", self.time_input)

        # Días de la semana (para semanal)
        self.days_of_week_label = QLabel("Días de la Semana:")
        self.days_of_week_list = QListWidget()
        self.days_of_week_list.setSelectionMode(QListWidget.MultiSelection)
        for i in range(7):
            item = QListWidgetItem(DAYS_OF_WEEK[i])
            item.setData(Qt.UserRole, i) # Guardar el índice del día
            self.days_of_week_list.addItem(item)
        self.days_of_week_list.setFixedHeight(100) # Altura fija para la lista
        self.form_layout.addRow(self.days_of_week_label, self.days_of_week_list)

        # Día del mes (para mensual)
        self.day_of_month_label = QLabel("Día del Mes:")
        self.day_of_month_input = QSpinBox()
        self.day_of_month_input.setRange(1, 31)
        self.day_of_month_input.setValue(1)
        self.form_layout.addRow(self.day_of_month_label, self.day_of_month_input)

        # Estado activo
        self.is_active_checkbox = QCheckBox("Activa")
        self.is_active_checkbox.setChecked(True)
        self.form_layout.addRow("Estado:", self.is_active_checkbox)

        self.main_layout.addLayout(self.form_layout)

        # Botones de acción
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).clicked.connect(self._save_schedule)
        self.buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        self._on_schedule_type_changed() # Inicializar visibilidad de campos

    def load_configs_for_combo(self):
        """Carga las configuraciones de base de datos en el combobox."""
        self.config_combo.clear()
        configs = backup_config_repository.get_all()
        if not configs:
            self.config_combo.addItem("No hay configuraciones disponibles", None)
            self.config_combo.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Save).setEnabled(False)
            notification_service.show_warning("Advertencia", "No hay configuraciones de base de datos. Por favor, añada una primero.")
            logger.warning("No hay configuraciones de base de datos para programar.")
            return

        for config in configs:
            self.config_combo.addItem(f"{config.name} (ID: {config.id})", config.id)
        self.config_combo.setEnabled(True)
        self.buttons.button(QDialogButtonBox.Save).setEnabled(True)
        logger.debug(f"Cargadas {len(configs)} configuraciones en el combobox de programación.")

    def _on_schedule_type_changed(self):
        """Ajusta la visibilidad de los campos según el tipo de programación seleccionado."""
        schedule_type = self.schedule_type_combo.currentText().lower()
        
        self.days_of_week_label.setVisible(schedule_type == SCHEDULE_TYPE_WEEKLY)
        self.days_of_week_list.setVisible(schedule_type == SCHEDULE_TYPE_WEEKLY)
        
        self.day_of_month_label.setVisible(schedule_type == SCHEDULE_TYPE_MONTHLY)
        self.day_of_month_input.setVisible(schedule_type == SCHEDULE_TYPE_MONTHLY)
        logger.debug(f"Tipo de programación cambiado a: {schedule_type}")

    def _load_schedule_data(self, schedule: BackupSchedule):
        """Carga los datos de una programación existente en el formulario."""
        # Seleccionar la configuración en el combobox
        index = self.config_combo.findData(schedule.config_id)
        if index != -1:
            self.config_combo.setCurrentIndex(index)
        else:
            # Si la configuración no se encuentra (ej. fue eliminada), deshabilitar el combobox
            self.config_combo.addItem(f"ID {schedule.config_id} (No encontrado)", schedule.config_id)
            self.config_combo.setCurrentIndex(self.config_combo.count() - 1)
            self.config_combo.setEnabled(False)
            logger.warning(f"Configuración ID {schedule.config_id} no encontrada para la programación.")

        self.schedule_type_combo.setCurrentText(schedule.schedule_type.capitalize())
        self.time_input.setText(schedule.time)
        
        # Seleccionar días de la semana
        for i in range(self.days_of_week_list.count()):
            item = self.days_of_week_list.item(i)
            if item.data(Qt.UserRole) in schedule.days_of_week:
                item.setSelected(True)
            else:
                item.setSelected(False)
        
        if schedule.day_of_month:
            self.day_of_month_input.setValue(schedule.day_of_month)
        
        self.is_active_checkbox.setChecked(schedule.is_active)
        self._on_schedule_type_changed() # Actualizar visibilidad
        logger.info(f"Programación ID {schedule.id} cargada en el formulario.")

    def _get_schedule_from_form(self) -> BackupSchedule:
        """Crea un objeto BackupSchedule a partir de los datos del formulario."""
        selected_config_id = self.config_combo.currentData()
        
        days_of_week = []
        for item in self.days_of_week_list.selectedItems():
            days_of_week.append(item.data(Qt.UserRole))
        
        schedule = BackupSchedule(
            id=self.current_schedule.id if self.current_schedule else None,
            config_id=selected_config_id if selected_config_id else 0,
            schedule_type=self.schedule_type_combo.currentText().lower(),
            time=self.time_input.text(),
            days_of_week=days_of_week if self.schedule_type_combo.currentText().lower() == SCHEDULE_TYPE_WEEKLY else None,
            day_of_month=self.day_of_month_input.value() if self.schedule_type_combo.currentText().lower() == SCHEDULE_TYPE_MONTHLY else None,
            is_active=self.is_active_checkbox.isChecked()
        )
        return schedule

    def _save_schedule(self):
        """Guarda la programación actual (crea o actualiza)."""
        schedule = self._get_schedule_from_form()
        
        is_valid, message = schedule.validate()
        if not is_valid:
            notification_service.show_warning("Error de Validación", message)
            logger.warning(f"Error de validación al guardar programación: {message}")
            return

        from ...services.scheduler_service import scheduler_service # Importar aquí para evitar circular
        if schedule.id is None:
            # Crear nueva programación
            new_schedule = scheduler_service.add_schedule(schedule)
            if new_schedule:
                notification_service.show_info("Éxito", "Programación guardada exitosamente.")
                self.schedule_saved.emit()
                self.accept()
                logger.info(f"Nueva programación para config_id {new_schedule.config_id} creada.")
            else:
                notification_service.show_error("Error", "No se pudo guardar la programación.")
                logger.error(f"Fallo al crear nueva programación para config_id: {schedule.config_id}")
        else:
            # Actualizar programación existente
            if scheduler_service.update_schedule(schedule):
                notification_service.show_info("Éxito", "Programación actualizada exitosamente.")
                self.schedule_saved.emit()
                self.accept()
                logger.info(f"Programación ID {schedule.id} actualizada.")
            else:
                notification_service.show_error("Error", "No se pudo actualizar la programación.")
                logger.error(f"Fallo al actualizar programación ID: {schedule.id}")
