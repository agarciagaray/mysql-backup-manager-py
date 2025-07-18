import tkinter as tk
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from datetime import datetime
import threading
import time
from typing import Optional
import logging
from PyQt5.QtWidgets import QStatusBar, QLabel
from PyQt5.QtCore import QTimer, QDateTime, Qt, QThread, pyqtSignal
from ...services.scheduler_service import scheduler_service
from ...repositories.backup_history_repository import backup_history_repository
from ...utils.helpers import format_bytes, format_duration

logger = logging.getLogger(__name__)

class TimeUpdateThread(QThread):
    """Hilo para actualizar la hora y el estado del scheduler cada segundo."""
    update_signal = pyqtSignal(str, str, str, str) # current_time, next_backup, last_backup, total_size

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self.scheduler_service = scheduler_service
        self.history_repo = backup_history_repository
        logger.debug("Hilo de actualización de tiempo inicializado.")

    def run(self):
        while self._running:
            current_time = QDateTime.currentDateTime().toString(Qt.DefaultLocaleLongDate)
            
            next_backup_time = self.scheduler_service.get_next_run_time()
            next_backup_str = next_backup_time.strftime("%Y-%m-%d %H:%M:%S") if next_backup_time else "N/A"

            last_backup_obj = self.history_repo.get_last_backup_time()
            last_backup_str = last_backup_obj.strftime("%Y-%m-%d %H:%M:%S") if last_backup_obj else "N/A"

            total_size = self.history_repo.get_total_backup_size()
            total_size_str = format_bytes(total_size)

            self.update_signal.emit(current_time, next_backup_str, last_backup_str, total_size_str)
            self.msleep(1000) # Actualizar cada segundo

    def stop(self):
        self._running = False
        self.wait() # Esperar a que el hilo termine
        logger.debug("Hilo de actualización de tiempo detenido.")

class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler_service = scheduler_service
        self.history_repo = backup_history_repository
        self._init_ui()
        self._start_update_thread()
        logger.info("Barra de estado inicializada.")

    def _init_ui(self):
        """Inicializa los elementos de la barra de estado."""
        self.current_time_label = QLabel("Hora: N/A")
        self.next_backup_label = QLabel("Próximo Respaldo: N/A")
        self.last_backup_label = QLabel("Último Respaldo: N/A")
        self.total_size_label = QLabel("Tamaño Total: N/A")
        self.scheduler_status_label = QLabel("Scheduler: Detenido")

        self.addPermanentWidget(self.current_time_label)
        self.addPermanentWidget(self.next_backup_label)
        self.addPermanentWidget(self.last_backup_label)
        self.addPermanentWidget(self.total_size_label)
        self.addPermanentWidget(self.scheduler_status_label)

    def _start_update_thread(self):
        """Inicia el hilo para actualizar la información de la barra de estado."""
        self.update_thread = TimeUpdateThread()
        self.update_thread.update_signal.connect(self._update_labels)
        self.update_thread.start()

    def _update_labels(self, current_time: str, next_backup: str, last_backup: str, total_size: str):
        """Actualiza las etiquetas de la barra de estado."""
        self.current_time_label.setText(f"Hora: {current_time}")
        self.next_backup_label.setText(f"Próximo Respaldo: {next_backup}")
        self.last_backup_label.setText(f"Último Respaldo: {last_backup}")
        self.total_size_label.setText(f"Tamaño Total: {total_size}")

    def update_scheduler_status(self, is_running: bool):
        """Actualiza el estado del scheduler en la barra de estado."""
        status_text = "Ejecutándose" if is_running else "Detenido"
        self.scheduler_status_label.setText(f"Scheduler: {status_text}")
        logger.debug(f"Estado del scheduler en barra de estado actualizado a: {status_text}")

    def close_event_thread(self):
        """Detiene el hilo de actualización cuando la aplicación se cierra."""
        if self.update_thread.isRunning():
            self.update_thread.stop()
            logger.debug("Hilo de actualización de barra de estado detenido al cerrar.")
