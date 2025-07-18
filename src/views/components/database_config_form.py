import logging
import os
from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QFileDialog, QLabel, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from ...models.backup_config import BackupConfig
from ...services.encryption_service import encryption_service
from ...utils.validators import is_valid_port, is_valid_path, is_valid_file_path, is_valid_retention_days, is_valid_host
from ...utils.constants import COMPRESSION_METHODS
from ...utils.helpers import get_mysqldump_default_path, get_icon
from .connection_tester import ConnectionTester
from .table_selector import TableSelector

logger = logging.getLogger(__name__)

class DatabaseConfigForm(QWidget):
    config_saved = pyqtSignal(BackupConfig)
    config_deleted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.encryption_service = encryption_service
        self.current_config: Optional[BackupConfig] = None
        self._init_ui()
        logger.info("Formulario de configuración de base de datos inicializado.")

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignRight)

        # Campos del formulario
        self.id_label = QLabel("ID: N/A")
        self.form_layout.addRow("ID:", self.id_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre único para la configuración")
        self.form_layout.addRow("Nombre:", self.name_input)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Ej: localhost o 127.0.0.1")
        self.form_layout.addRow("Host:", self.host_input)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(3306)
        self.form_layout.addRow("Puerto:", self.port_input)

        self.username_input = QLineEdit()
        self.form_layout.addRow("Usuario:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.form_layout.addRow("Contraseña:", self.password_input)

        self.database_name_input = QLineEdit()
        self.form_layout.addRow("Nombre DB:", self.database_name_input)

        # mysqldump path
        mysqldump_layout = QHBoxLayout()
        self.mysqldump_path_input = QLineEdit()
        self.mysqldump_path_input.setPlaceholderText("Ruta al ejecutable mysqldump")
        self.mysqldump_path_input.setText(get_mysqldump_default_path()) # Ruta por defecto
        mysqldump_layout.addWidget(self.mysqldump_path_input)
        self.mysqldump_browse_button = QPushButton(get_icon("folder"), "")
        self.mysqldump_browse_button.setFixedSize(30, 30)
        self.mysqldump_browse_button.clicked.connect(self._browse_mysqldump_path)
        mysqldump_layout.addWidget(self.mysqldump_browse_button)
        self.form_layout.addRow("Ruta mysqldump:", mysqldump_layout)

        # Backup path
        backup_path_layout = QHBoxLayout()
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setPlaceholderText("Ruta donde se guardarán los respaldos")
        backup_path_layout.addWidget(self.backup_path_input)
        self.backup_path_browse_button = QPushButton(get_icon("folder"), "")
        self.backup_path_browse_button.setFixedSize(30, 30)
        self.backup_path_browse_button.clicked.connect(self._browse_backup_path)
        backup_path_layout.addWidget(self.backup_path_browse_button)
        self.form_layout.addRow("Ruta Respaldo:", backup_path_layout)

        # Connection Tester
        self.connection_tester = ConnectionTester()
        self.form_layout.addRow("Probar Conexión:", self.connection_tester)

        # Table Selector
        self.table_selector = TableSelector()
        self.form_layout.addRow("Tablas a Excluir:", self.table_selector)
        
        # Botón para cargar tablas en el selector
        self.load_tables_button = QPushButton(get_icon("refresh"), "Cargar Tablas para Excluir")
        self.load_tables_button.clicked.connect(self._load_tables_for_selector)
        self.form_layout.addRow("", self.load_tables_button) # Fila sin etiqueta para el botón

        self.compression_method_combo = QComboBox()
        self.compression_method_combo.addItems(COMPRESSION_METHODS)
        self.form_layout.addRow("Compresión:", self.compression_method_combo)

        self.retention_days_main_input = QSpinBox()
        self.retention_days_main_input.setRange(0, 3650) # 10 años
        self.retention_days_main_input.setValue(7)
        self.form_layout.addRow("Retención (días):", self.retention_days_main_input)

        self.retention_days_segregated_input = QSpinBox()
        self.retention_days_segregated_input.setRange(0, 3650)
        self.retention_days_segregated_input.setValue(30)
        self.form_layout.addRow("Retención Segregada (días):", self.retention_days_segregated_input)

        self.is_active_checkbox = QCheckBox("Activa")
        self.is_active_checkbox.setChecked(True)
        self.form_layout.addRow("Estado:", self.is_active_checkbox)

        self.main_layout.addLayout(self.form_layout)

        # Botones de acción
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton(get_icon("save"), "Guardar")
        self.save_button.clicked.connect(self._save_config)
        self.button_layout.addWidget(self.save_button)

        self.delete_button = QPushButton(get_icon("delete"), "Eliminar")
        self.delete_button.clicked.connect(self._delete_config)
        self.delete_button.setEnabled(False) # Deshabilitado por defecto
        self.button_layout.addWidget(self.delete_button)

        self.clear_button = QPushButton(get_icon("clear"), "Limpiar")
        self.clear_button.clicked.connect(self.clear_form)
        self.button_layout.addWidget(self.clear_button)

        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addStretch(1) # Empuja el contenido hacia arriba

        # Conectar señales para actualizar el ConnectionTester y TableSelector
        self.host_input.textChanged.connect(self._update_tester_and_selector_config)
        self.port_input.valueChanged.connect(self._update_tester_and_selector_config)
        self.username_input.textChanged.connect(self._update_tester_and_selector_config)
        self.password_input.textChanged.connect(self._update_tester_and_selector_config)
        self.database_name_input.textChanged.connect(self._update_tester_and_selector_config)

    def _update_tester_and_selector_config(self):
        """Actualiza la configuración en ConnectionTester y TableSelector."""
        temp_config = self._get_config_from_form(is_validation_check=True)
        self.connection_tester.set_config(temp_config)
        self.table_selector.set_config(temp_config)
        logger.debug("Configuración actualizada en ConnectionTester y TableSelector.")

    def _browse_mysqldump_path(self):
        """Abre un diálogo para seleccionar la ruta del ejecutable mysqldump."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar mysqldump", "", "Ejecutables (*.exe);;Todos los archivos (*)")
        if file_path:
            self.mysqldump_path_input.setText(file_path)
            logger.debug(f"Ruta de mysqldump seleccionada: {file_path}")

    def _browse_backup_path(self):
        """Abre un diálogo para seleccionar la ruta de la carpeta de respaldos."""
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Respaldo")
        if dir_path:
            self.backup_path_input.setText(dir_path)
            logger.debug(f"Ruta de respaldo seleccionada: {dir_path}")

    def _load_tables_for_selector(self):
        """Carga las tablas en el TableSelector usando la configuración actual del formulario."""
        temp_config = self._get_config_from_form(is_validation_check=True)
        self.table_selector.set_config(temp_config) # Asegurarse de que el selector tenga la config más reciente
        self.table_selector._start_load_tables() # Llamar al método interno para iniciar la carga
        logger.info("Iniciando carga de tablas para el selector.")

    def load_config(self, config: BackupConfig):
        """Carga una configuración existente en el formulario."""
        self.current_config = config
        self.id_label.setText(f"ID: {config.id}")
        self.name_input.setText(config.name)
        self.host_input.setText(config.host)
        self.port_input.setValue(config.port)
        self.username_input.setText(config.username)
        self.password_input.setText(config.password_encrypted) # Contraseña desencriptada
        self.database_name_input.setText(config.database_name)
        self.mysqldump_path_input.setText(config.mysqldump_path)
        self.backup_path_input.setText(config.backup_path)
        self.compression_method_combo.setCurrentText(config.compression_method)
        self.retention_days_main_input.setValue(config.retention_days_main)
        self.retention_days_segregated_input.setValue(config.retention_days_segregated)
        self.is_active_checkbox.setChecked(config.is_active)
        
        self.delete_button.setEnabled(True)
        self.connection_tester.set_config(config)
        self.table_selector.set_config(config)
        self.table_selector.set_selected_tables(config.excluded_tables) # Pre-seleccionar tablas excluidas
        logger.info(f"Configuración '{config.name}' (ID: {config.id}) cargada en el formulario.")

    def clear_form(self):
        """Limpia todos los campos del formulario."""
        self.current_config = None
        self.id_label.setText("ID: N/A")
        self.name_input.clear()
        self.host_input.setText("localhost")
        self.port_input.setValue(3306)
        self.username_input.clear()
        self.password_input.clear()
        self.database_name_input.clear()
        self.mysqldump_path_input.setText(get_mysqldump_default_path())
        self.backup_path_input.clear()
        self.compression_method_combo.setCurrentText("zip")
        self.retention_days_main_input.setValue(7)
        self.retention_days_segregated_input.setValue(30)
        self.is_active_checkbox.setChecked(True)
        
        self.delete_button.setEnabled(False)
        self.connection_tester.set_config(BackupConfig()) # Resetear tester
        self.table_selector.set_config(BackupConfig()) # Resetear selector
        self.table_selector.available_tables_list.clear() # Limpiar lista de tablas
        logger.info("Formulario de configuración limpiado.")

    def _get_config_from_form(self, is_validation_check: bool = False) -> BackupConfig:
        """Crea un objeto BackupConfig a partir de los datos del formulario."""
        config = BackupConfig(
            id=self.current_config.id if self.current_config else None,
            name=self.name_input.text(),
            host=self.host_input.text(),
            port=self.port_input.value(),
            username=self.username_input.text(),
            password_encrypted=self.password_input.text(), # Aquí está desencriptada
            database_name=self.database_name_input.text(),
            mysqldump_path=self.mysqldump_path_input.text(),
            backup_path=self.backup_path_input.text(),
            excluded_tables=self.table_selector.get_selected_tables(),
            compression_method=self.compression_method_combo.currentText(),
            retention_days_main=self.retention_days_main_input.value(),
            retention_days_segregated=self.retention_days_segregated_input.value(),
            is_active=self.is_active_checkbox.isChecked()
        )
        # Si es solo para validación, no actualizar created_at/updated_at
        if is_validation_check and self.current_config:
            config.created_at = self.current_config.created_at
            config.updated_at = self.current_config.updated_at
        return config

    def _save_config(self):
        """Guarda la configuración actual (crea o actualiza)."""
        config = self._get_config_from_form()
        
        is_valid, message = config.validate()
        if not is_valid:
            notification_service.show_warning("Error de Validación", message)
            logger.warning(f"Error de validación al guardar configuración: {message}")
            return

        from ...repositories.backup_config_repository import backup_config_repository
        if config.id is None:
            # Crear nueva configuración
            new_config = backup_config_repository.add(config)
            if new_config:
                self.load_config(new_config) # Cargar la nueva config con su ID
                notification_service.show_info("Éxito", f"Configuración '{new_config.name}' guardada exitosamente.")
                self.config_saved.emit(new_config)
                logger.info(f"Nueva configuración '{new_config.name}' creada.")
            else:
                notification_service.show_error("Error", f"No se pudo guardar la configuración '{config.name}'. Puede que ya exista un nombre igual.")
                logger.error(f"Fallo al crear nueva configuración: {config.name}")
        else:
            # Actualizar configuración existente
            if backup_config_repository.update(config):
                notification_service.show_info("Éxito", f"Configuración '{config.name}' actualizada exitosamente.")
                self.config_saved.emit(config)
                logger.info(f"Configuración '{config.name}' (ID: {config.id}) actualizada.")
            else:
                notification_service.show_error("Error", f"No se pudo actualizar la configuración '{config.name}'.")
                logger.error(f"Fallo al actualizar configuración: {config.name} (ID: {config.id})")

    def _delete_config(self):
        """Elimina la configuración actual."""
        if self.current_config and self.current_config.id is not None:
            reply = notification_service.ask_yes_no(
                "Confirmar Eliminación",
                f"¿Está seguro que desea eliminar la configuración '{self.current_config.name}'?\n"
                "Esto también eliminará las programaciones y el historial asociados."
            )
            if reply:
                from ...repositories.backup_config_repository import backup_config_repository
                if backup_config_repository.delete(self.current_config.id):
                    notification_service.show_info("Éxito", "Configuración eliminada exitosamente.")
                    self.config_deleted.emit(self.current_config.id)
                    self.clear_form()
                    logger.info(f"Configuración '{self.current_config.name}' (ID: {self.current_config.id}) eliminada.")
                else:
                    notification_service.show_error("Error", "No se pudo eliminar la configuración.")
                    logger.error(f"Fallo al eliminar configuración: {self.current_config.name} (ID: {self.current_config.id})")
        else:
            notification_service.show_warning("Advertencia", "No hay configuración seleccionada para eliminar.")
            logger.warning("Intento de eliminar sin configuración seleccionada.")
