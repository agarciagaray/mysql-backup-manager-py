import logging
from typing import Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QDialog, QDialogButtonBox, QFormLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from ...repositories.backup_config_repository import backup_config_repository
from ...services.notification_service import notification_service
from ...utils.helpers import get_icon

logger = logging.getLogger(__name__)

class ForceBackupDialog(QDialog):
    """Diálogo para seleccionar una configuración y forzar un respaldo."""
    backup_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Forzar Respaldo Ahora")
        self.setFixedSize(350, 150)
        self.config_repo = backup_config_repository
        self._init_ui()
        self.load_configs()
        logger.info("Diálogo de forzar respaldo inicializado.")

    def _init_ui(self):
        layout = QFormLayout(self)
        
        self.config_combo = QComboBox()
        layout.addRow("Seleccione configuración:", self.config_combo)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def load_configs(self):
        """Carga las configuraciones de base de datos en el combobox."""
        self.config_combo.clear()
        self.configs = self.config_repo.get_all()
        if not self.configs:
            self.config_combo.addItem("No hay configuraciones disponibles")
            self.config_combo.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            logger.warning("No hay configuraciones de base de datos para forzar respaldo.")
            return

        for config in self.configs:
            self.config_combo.addItem(f"{config.name} (ID: {config.id})", config.id)
        self.config_combo.setEnabled(True)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        logger.debug(f"Cargadas {len(self.configs)} configuraciones en el diálogo de forzar respaldo.")

    def _on_accept(self):
        selected_id = self.config_combo.currentData()
        if selected_id is None:
            notification_service.show_warning("Error", "Por favor, seleccione una configuración.")
            return
        self.backup_selected.emit(selected_id)
        self.accept()

class QuickActions(QWidget):
    force_backup_triggered = pyqtSignal(int) # Emite el config_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_repo = backup_config_repository
        self._init_ui()
        self.load_configs() # Cargar configs para el diálogo de forzar respaldo
        logger.info("Widget de Acciones Rápidas inicializado.")

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("Acciones Rápidas")
        title_label.setFont(self.font())
        title_label.setStyleSheet("font-weight: bold;")
        self.main_layout.addWidget(title_label)

        self.force_backup_button = QPushButton(get_icon("play"), "Forzar Respaldo Ahora")
        self.force_backup_button.clicked.connect(self._open_force_backup_dialog)
        self.main_layout.addWidget(self.force_backup_button)

        self.manage_configs_button = QPushButton(get_icon("database"), "Gestionar Configuraciones")
        self.manage_configs_button.clicked.connect(lambda: self._navigate_to_tab(1)) # Pestaña de Configuraciones DB
        self.main_layout.addWidget(self.manage_configs_button)

        self.view_history_button = QPushButton(get_icon("history"), "Ver Historial de Respaldos")
        self.view_history_button.clicked.connect(lambda: self._navigate_to_tab(3)) # Pestaña de Logs (Historial)
        self.main_layout.addWidget(self.view_history_button)

        self.main_layout.addStretch(1) # Empuja los botones hacia arriba

    def load_configs(self):
        """Carga las configuraciones para el diálogo de forzar respaldo."""
        # No es necesario cargar aquí, el diálogo lo hace al abrirse.
        pass

    def _open_force_backup_dialog(self):
        """Abre el diálogo para forzar un respaldo."""
        dialog = ForceBackupDialog(self)
        dialog.backup_selected.connect(self.force_backup_triggered.emit)
        dialog.exec_()
        logger.debug("Diálogo de forzar respaldo cerrado.")

    def _navigate_to_tab(self, index: int):
        """Navega a la pestaña especificada en la ventana principal."""
        # Acceder a la ventana principal para cambiar de pestaña
        main_window = self.window() # Obtiene la QMainWindow
        if main_window and hasattr(main_window, 'tab_widget'):
            main_window.tab_widget.setCurrentIndex(index)
            logger.info(f"Navegando a la pestaña {index}.")
        else:
            logger.warning("No se pudo navegar a la pestaña. Estructura de parentela inesperada.")
