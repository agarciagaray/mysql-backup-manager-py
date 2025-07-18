"""
Componente para probar la conexión a una base de datos MySQL/MariaDB
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import logging
import mysql.connector
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from ...models.backup_config import BackupConfig
from ...services.encryption_service import encryption_service
from ...utils.helpers import get_icon

logger = logging.getLogger(__name__)

class ConnectionTestThread(QThread):
    """Hilo para probar la conexión a la base de datos."""
    test_result = pyqtSignal(bool, str)

    def __init__(self, config: BackupConfig, parent=None):
        super().__init__(parent)
        self.config = config
        logger.debug(f"Hilo de prueba de conexión creado para {config.name}.")

    def run(self):
        try:
            # Usar la contraseña desencriptada que viene del modelo
            cnx = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password_encrypted,
                database=self.config.database_name,
                connection_timeout=5 # Timeout de 5 segundos
            )
            cnx.close()
            self.test_result.emit(True, "Conexión exitosa.")
            logger.info(f"Prueba de conexión exitosa para {self.config.name}.")
        except mysql.connector.Error as err:
            error_message = f"Error de conexión: {err}"
            self.test_result.emit(False, error_message)
            logger.error(f"Prueba de conexión fallida para {self.config.name}: {err}")
        except Exception as e:
            error_message = f"Error inesperado: {e}"
            self.test_result.emit(False, error_message)
            logger.error(f"Prueba de conexión fallida (inesperado) para {self.config.name}: {e}")

class ConnectionTester(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.encryption_service = encryption_service
        self.current_config: Optional[BackupConfig] = None
        self._init_ui()
        logger.info("Widget de prueba de conexión inicializado.")

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        self.test_button = QPushButton(get_icon("connect"), "Probar Conexión")
        self.test_button.clicked.connect(self._start_test)
        self.main_layout.addWidget(self.test_button)

        self.status_label = QLabel("Estado: Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_label)

    def set_config(self, config: BackupConfig):
        """Establece la configuración de la base de datos a probar."""
        self.current_config = config
        self.status_label.setText("Estado: Listo")
        self.status_label.setStyleSheet("") # Limpiar estilo anterior
        logger.debug(f"Configuración de conexión establecida para {config.name}.")

    def _start_test(self):
        """Inicia la prueba de conexión en un hilo separado."""
        if not self.current_config:
            self.status_label.setText("Estado: No hay configuración para probar.")
            self.status_label.setStyleSheet("color: orange;")
            logger.warning("Intento de prueba de conexión sin configuración establecida.")
            return

        self.status_label.setText("Estado: Probando conexión...")
        self.status_label.setStyleSheet("color: blue;")
        self.test_button.setEnabled(False) # Deshabilitar botón durante la prueba

        # Crear y ejecutar el hilo de prueba
        self.test_thread = ConnectionTestThread(self.current_config)
        self.test_thread.test_result.connect(self._on_test_result)
        self.test_thread.start()
        logger.info(f"Iniciando prueba de conexión para {self.current_config.name}.")

    def _on_test_result(self, success: bool, message: str):
        """Maneja el resultado de la prueba de conexión."""
        self.test_button.setEnabled(True) # Habilitar botón
        self.status_label.setText(f"Estado: {message}")
        if success:
            self.status_label.setStyleSheet("color: green;")
            logger.info(f"Prueba de conexión finalizada: Éxito. {message}")
        else:
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"Prueba de conexión finalizada: Fallida. {message}")
