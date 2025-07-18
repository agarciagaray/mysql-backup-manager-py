"""
Componente para mostrar el estado del servicio de programación
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from datetime import datetime
from typing import Callable, Any, Optional
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from ...services.scheduler_service import scheduler_service
from ...repositories.backup_history_repository import backup_history_repository
from ...utils.helpers import format_timedelta, format_duration, get_icon

logger = logging.getLogger(__name__)

class SchedulerStatus(ttk_bs.LabelFrame):
    def __init__(self, master, action_callback: Callable[[str], None]):
        super().__init__(master, text="Estado del Programador de Respaldos", bootstyle=INFO)
        self.action_callback = action_callback
        self.status_data: Dict[str, Any] = {}
        self._create_widgets()
        self.scheduler_service = scheduler_service
        self.history_repo = backup_history_repository
        self._setup_timer()
        self.update_status() # Cargar estado inicial
        logger.info("SchedulerStatus inicializado.")

    def _create_widgets(self):
        """Crea los widgets para mostrar el estado y los controles."""
        # Frame para la información de estado
        info_frame = ttk_bs.Frame(self)
        info_frame.pack(fill=X, padx=10, pady=5)

        # Estado del servicio
        ttk_bs.Label(info_frame, text="Servicio:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W, pady=2)
        self.service_status_label = ttk_bs.Label(info_frame, text="Detenido", bootstyle=DANGER)
        self.service_status_label.grid(row=0, column=1, sticky=W, padx=5, pady=2)

        # Total de trabajos
        ttk_bs.Label(info_frame, text="Total de Trabajos:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=W, pady=2)
        self.total_jobs_label = ttk_bs.Label(info_frame, text="0")
        self.total_jobs_label.grid(row=1, column=1, sticky=W, padx=5, pady=2)

        # Trabajos activos
        ttk_bs.Label(info_frame, text="Trabajos Activos:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=W, pady=2)
        self.active_jobs_label = ttk_bs.Label(info_frame, text="0")
        self.active_jobs_label.grid(row=2, column=1, sticky=W, padx=5, pady=2)

        # Próximo Respaldo
        ttk_bs.Label(info_frame, text="Próximo Respaldo:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=W, pady=2)
        self.next_backup_label = ttk_bs.Label(info_frame, text="N/A")
        self.next_backup_label.grid(row=3, column=1, sticky=W, padx=5, pady=2)

        # Última ejecución exitosa
        ttk_bs.Label(info_frame, text="Último Respaldo Exitoso:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=W, pady=2)
        self.last_run_label = ttk_bs.Label(info_frame, text="N/A")
        self.last_run_label.grid(row=4, column=1, sticky=W, padx=5, pady=2)

        # Frame para los botones de control
        buttons_frame = ttk_bs.Frame(self)
        buttons_frame.pack(fill=X, padx=10, pady=5)

        self.start_btn = ttk_bs.Button(
            buttons_frame,
            text="▶️ Iniciar",
            command=lambda: self.action_callback("start"),
            bootstyle=SUCCESS
        )
        self.start_btn.pack(side=LEFT, padx=2)

        self.stop_btn = ttk_bs.Button(
            buttons_frame,
            text="⏹️ Detener",
            command=lambda: self.action_callback("stop"),
            bootstyle=DANGER
        )
        self.stop_btn.pack(side=LEFT, padx=2)

        self.pause_btn = ttk_bs.Button(
            buttons_frame,
            text="⏸️ Pausar Todos",
            command=lambda: self.action_callback("pause"),
            bootstyle=WARNING
        )
        self.pause_btn.pack(side=LEFT, padx=2)

        self.resume_btn = ttk_bs.Button(
            buttons_frame,
            text="⏯️ Reanudar Todos",
            command=lambda: self.action_callback("resume"),
            bootstyle=INFO
        )
        self.resume_btn.pack(side=LEFT, padx=2)

        self.setStyleSheet("""
            SchedulerStatus {
                background-color: #e8f0fe;
                border-radius: 8px;
                border: 1px solid #c0d8f8;
            }
            SchedulerStatus QLabel {
                color: #2c3e50;
            }
            SchedulerStatus QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            SchedulerStatus QPushButton:hover {
                background-color: #45a049;
            }
            SchedulerStatus QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    def _setup_timer(self):
        """Configura un temporizador para actualizar el estado periódicamente."""
        self.timer = QTimer(self)
        self.timer.setInterval(5000) # Actualizar cada 5 segundos
        self.timer.timeout.connect(self.update_status)
        self.timer.start()

    def update_status(self):
        """Actualiza la información de estado del scheduler."""
        is_running = self.scheduler_service.is_running()
        self.service_status_label.config(text="En Ejecución" if is_running else "Detenido", bootstyle=SUCCESS if is_running else DANGER)
        
        total_jobs = self.scheduler_service.get_total_jobs()
        active_jobs = self.scheduler_service.get_active_jobs()
        next_backup = self.scheduler_service.get_next_run_time()

        # Actualizar conteos de trabajos
        self.total_jobs_label.config(text=str(total_jobs))
        self.active_jobs_label.config(text=str(active_jobs))

        # Actualizar próximo respaldo
        if next_backup:
            time_until_next = next_backup - datetime.now()
            if time_until_next.total_seconds() > 0:
                self.next_backup_label.config(text=f"{next_backup.strftime('%Y-%m-%d %H:%M:%S')} (en {format_duration(time_until_next)})")
            else:
                self.next_backup_label.config(text=f"{next_backup.strftime('%Y-%m-%d %H:%M:%S')} (próximamente)")
        else:
            self.next_backup_label.config(text="N/A")
        
        # Actualizar último respaldo exitoso
        last_backup_time = self.history_repo.get_last_backup_time()
        self.last_run_label.config(text=last_backup_time.strftime("%Y-%m-%d %H:%M:%S") if last_backup_time else "N/A")

        # Habilitar/deshabilitar botones
        self.start_btn.config(state=DISABLED if is_running else NORMAL)
        self.stop_btn.config(state=NORMAL if is_running else DISABLED)
        self.pause_btn.config(state=NORMAL if is_running and active_jobs > 0 else DISABLED)
        self.resume_btn.config(state=NORMAL if is_running and self.scheduler_service.scheduler.state != 2 else DISABLED) # 2 = paused
        
        logger.debug("SchedulerStatus actualizado.")

class SchedulerStatusWidget(QWidget):
    # Señales para comunicar acciones al servicio de scheduler
    start_scheduler_triggered = pyqtSignal()
    stop_scheduler_triggered = pyqtSignal()
    pause_scheduler_triggered = pyqtSignal()
    resume_scheduler_triggered = pyqtSignal()
    # Señal para notificar cambios en el estado del scheduler (para la UI principal)
    scheduler_status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler_service = scheduler_service
        self._init_ui()
        self.update_status() # Cargar estado inicial
        self._start_auto_refresh()
        logger.info("Widget de estado del Scheduler inicializado.")

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("Estado del Programador")
        title_label.setFont(self.font())
        title_label.setStyleSheet("font-weight: bold;")
        self.main_layout.addWidget(title_label)

        # Contenedor para el estado actual
        status_frame = QFrame(self)
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setFrameShadow(QFrame.Raised)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setSpacing(5)

        self.status_label = QLabel("Estado: N/A")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)

        self.total_jobs_label = QLabel("Total de trabajos: 0")
        status_layout.addWidget(self.total_jobs_label)

        self.active_jobs_label = QLabel("Trabajos activos: 0")
        status_layout.addWidget(self.active_jobs_label)

        self.next_backup_label = QLabel("Próximo respaldo: N/A")
        status_layout.addWidget(self.next_backup_label)

        self.main_layout.addWidget(status_frame)

        # Contenedor para los botones de control
        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)
        control_layout.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton(get_icon("play"), "Iniciar")
        self.start_button.clicked.connect(self.start_scheduler_triggered.emit)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton(get_icon("stop"), "Detener")
        self.stop_button.clicked.connect(self.stop_scheduler_triggered.emit)
        control_layout.addWidget(self.stop_button)

        self.pause_button = QPushButton(get_icon("pause"), "Pausar")
        self.pause_button.clicked.connect(self.pause_scheduler_triggered.emit)
        control_layout.addWidget(self.pause_button)

        self.resume_button = QPushButton(get_icon("resume"), "Reanudar")
        self.resume_button.clicked.connect(self.resume_scheduler_triggered.emit)
        control_layout.addWidget(self.resume_button)

        self.main_layout.addLayout(control_layout)
        self.main_layout.addStretch(1) # Empuja el contenido hacia arriba

    def update_status(self):
        """Actualiza la información del estado del scheduler."""
        logger.debug("Actualizando estado del Scheduler Widget...")
        status_data = self.scheduler_service.get_scheduler_status()
        
        is_running = status_data['is_running']
        total_jobs = status_data['total_jobs']
        active_jobs = status_data['active_jobs']
        next_backup_time = status_data['next_backup']

        # Actualizar etiquetas de estado
        status_text = "Ejecutándose" if is_running else "Detenido"
        if is_running and self.scheduler_service.scheduler.running and self.scheduler_service.scheduler.paused:
            status_text = "Pausado"
        
        self.status_label.setText(f"Estado: {status_text}")
        self.status_label.setStyleSheet(f"color: {'green' if is_running and not self.scheduler_service.scheduler.paused else ('orange' if is_running and self.scheduler_service.scheduler.paused else 'red')}; font-weight: bold;")

        self.total_jobs_label.setText(f"Total de trabajos: {total_jobs}")
        self.active_jobs_label.setText(f"Trabajos activos: {active_jobs}")
        self.next_backup_label.setText(f"Próximo respaldo: {next_backup_time.strftime('%Y-%m-%d %H:%M:%S') if next_backup_time else 'N/A'}")

        # Habilitar/deshabilitar botones
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.pause_button.setEnabled(is_running and not self.scheduler_service.scheduler.paused)
        self.resume_button.setEnabled(is_running and self.scheduler_service.scheduler.paused)
        
        self.scheduler_status_changed.emit(is_running) # Emitir señal para la ventana principal
        logger.debug("Estado del Scheduler Widget actualizado.")

    def _start_auto_refresh(self):
        """Inicia el refresco automático del widget."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_status)
        self.refresh_timer.start(5000) # Refrescar cada 5 segundos
        logger.debug("Auto-refresco del Scheduler Widget iniciado.")

    def stop_auto_refresh(self):
        """Detiene el refresco automático del widget."""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            logger.debug("Auto-refresco del Scheduler Widget detenido.")
