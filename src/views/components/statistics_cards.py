import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt
from datetime import datetime

from ...repositories.backup_history_repository import backup_history_repository
from ...repositories.backup_config_repository import backup_config_repository
from ...utils.helpers import format_bytes, format_duration, get_icon

logger = logging.getLogger(__name__)

class StatisticsCard(QFrame):
    def __init__(self, title: str, value: str, icon_name: str = None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setContentsMargins(10, 10, 10, 10)
        self.setFixedSize(200, 120) # Tamaño fijo para las tarjetas

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(5)

        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name).pixmap(32, 32)) # Tamaño del icono
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        self.setStyleSheet("""
            StatisticsCard {
                background-color: #f0f0f0;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            StatisticsCard QLabel {
                color: #333333;
            }
        """)

    def update_value(self, new_value: str):
        self.value_label.setText(new_value)

class StatisticsCards(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_repo = backup_history_repository
        self.config_repo = backup_config_repository
        self._init_ui()
        logger.info("Tarjetas de estadísticas inicializadas.")

    def _init_ui(self):
        """Inicializa el layout de las tarjetas de estadísticas."""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.total_backups_card = StatisticsCard("Total Respaldos", "0", "backup")
        self.main_layout.addWidget(self.total_backups_card)

        self.successful_backups_card = StatisticsCard("Respaldos Exitosos", "0", "success")
        self.main_layout.addWidget(self.successful_backups_card)

        self.failed_backups_card = StatisticsCard("Respaldos Fallidos", "0", "error")
        self.main_layout.addWidget(self.failed_backups_card)

        self.total_configs_card = StatisticsCard("Configuraciones DB", "0", "database")
        self.main_layout.addWidget(self.total_configs_card)

        self.last_backup_card = StatisticsCard("Último Respaldo", "N/A", "calendar")
        self.main_layout.addWidget(self.last_backup_card)

        self.total_size_card = StatisticsCard("Tamaño Total Respaldos", "0 B", "storage")
        self.main_layout.addWidget(self.total_size_card)

        self.main_layout.addStretch(1) # Empuja las tarjetas a la izquierda

    def update_data(self):
        """Actualiza los datos de todas las tarjetas de estadísticas."""
        logger.debug("Actualizando datos de tarjetas de estadísticas...")
        total_backups = self.history_repo.get_total_backups()
        successful_backups = self.history_repo.get_successful_backups()
        failed_backups = self.history_repo.get_failed_backups()
        total_configs = len(self.config_repo.get_all())
        last_backup_time = self.history_repo.get_last_backup_time()
        total_backup_size = self.history_repo.get_total_backup_size()

        self.total_backups_card.update_value(str(total_backups))
        self.successful_backups_card.update_value(str(successful_backups))
        self.failed_backups_card.update_value(str(failed_backups))
        self.total_configs_card.update_value(str(total_configs))
        self.last_backup_card.update_value(last_backup_time.strftime("%Y-%m-%d %H:%M") if last_backup_time else "N/A")
        self.total_size_card.update_value(format_bytes(total_backup_size))
        logger.debug("Datos de tarjetas de estadísticas actualizados.")
