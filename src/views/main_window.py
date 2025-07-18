"""
Ventana principal de la aplicación
"""
import logging
import os
import sys
import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from PyQt5.QtCore import QDateTime, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QMainWindow,
                             QMessageBox, QTabWidget, QToolBar, QVBoxLayout,
                             QWidget)
from ttkbootstrap.constants import *

from ..repositories.app_settings_repository import app_settings_repository
from ..repositories.backup_history_repository import backup_history_repository
from ..services.notification_service import notification_service
from ..services.scheduler_service import scheduler_service
from ..utils.constants import APP_NAME, APP_VERSION
from ..utils.helpers import (copy_assets_to_app_data, format_bytes,
                             format_duration, get_app_data_path, get_icon,
                             setup_logging)
from .backup_history import BackupHistoryView
from .backup_scheduler import BackupSchedulerView
from .dashboard import DashboardView
from .database_config import DatabaseConfigView
from .logs_viewer import LogsViewerView
from .settings_dialog import SettingsView

ASSETS_PATH = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))), 'assets', 'icons')

logger = logging.getLogger(__name__)


class TimeUpdateThread(QThread):
    """Hilo para actualizar la hora y el estado del scheduler cada segundo."""
    update_signal = pyqtSignal(
        str, str, str, str)  # current_time, next_backup, last_backup, total_size

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
            next_backup_str = next_backup_time.strftime(
                "%Y-%m-%d %H:%M:%S") if next_backup_time else "N/A"

            last_backup_obj = self.history_repo.get_last_backup_time()
            last_backup_str = last_backup_obj.strftime(
                "%Y-%m-%d %H:%M:%S") if last_backup_obj else "N/A"

            total_size = self.history_repo.get_total_backup_size()
            total_size_str = format_bytes(total_size)

            self.update_signal.emit(
                current_time, next_backup_str, last_backup_str, total_size_str)
            self.msleep(1000)  # Actualizar cada segundo

    def stop(self):
        self._running = False
        self.wait()  # Esperar a que el hilo termine
        logger.debug("Hilo de actualización de tiempo detenido.")


class Toolbar(QToolBar):
    export_triggered = pyqtSignal()
    import_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    about_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Barra de Herramientas", parent)
        self.setIconSize(QSize(24, 24))
        self._init_actions()
        logger.info("Barra de herramientas inicializada.")

    def _init_actions(self):
        """Inicializa las acciones de la barra de herramientas."""
        # Acción de Exportar
        export_action = QAction(get_icon("export"), "Exportar Datos", self)
        export_action.setToolTip(
            "Exportar todas las configuraciones y programaciones a un archivo.")
        export_action.triggered.connect(self.export_triggered.emit)
        self.addAction(export_action)

        # Acción de Importar
        import_action = QAction(get_icon("import"), "Importar Datos", self)
        import_action.setToolTip(
            "Importar configuraciones y programaciones desde un archivo.")
        import_action.triggered.connect(self.import_triggered.emit)
        self.addAction(import_action)

        self.addSeparator()

        # Acción de Ajustes
        settings_action = QAction(get_icon("settings"), "Ajustes", self)
        settings_action.setToolTip("Configurar los ajustes de la aplicación.")
        settings_action.triggered.connect(self.settings_triggered.emit)
        self.addAction(settings_action)

        # Acción de Acerca de
        about_action = QAction(get_icon("info"), "Acerca de", self)
        about_action.setToolTip("Información sobre la aplicación.")
        about_action.triggered.connect(self.about_triggered.emit)
        self.addAction(about_action)


class MainWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.theme = "darkly"
        self._build_ui()

    def _build_ui(self):
        # Barra superior
        self.topbar = ttk.Frame(self, style="primary.TFrame")
        self.topbar.pack(side=TOP, fill=X)

        # Logo
        logo_path = os.path.join(ASSETS_PATH, "app_icon.png")
        try:
            self.logo_img = tk.PhotoImage(file=logo_path)
            logo_label = ttk.Label(
                self.topbar, image=self.logo_img, style="primary.TLabel")
            logo_label.pack(side=LEFT, padx=10, pady=5)
        except Exception:
            logo_label = ttk.Label(
                self.topbar, text="🗄️", style="primary.TLabel", font=("Segoe UI", 18))
            logo_label.pack(side=LEFT, padx=10, pady=5)

        # Título
        title_label = ttk.Label(self.topbar, text="MySQL Backup Manager",
                                style="primary.TLabel", font=("Segoe UI", 16, "bold"))
        title_label.pack(side=LEFT, padx=10)

        # Botón para cambiar tema
        self.theme_btn = ttk.Button(
            self.topbar, text="🌙/☀️", command=self.toggle_theme, style="secondary.TButton")
        self.theme_btn.pack(side=RIGHT, padx=10)

        # Sidebar de navegación
        self.sidebar = ttk.Frame(self, style="secondary.TFrame", width=180)
        self.sidebar.pack(side=LEFT, fill=Y)
        self._build_sidebar()

        # Área principal
        self.main_content = ttk.Frame(self, style="TFrame")
        self.main_content.pack(side=LEFT, fill=BOTH, expand=YES)
        self.current_view = None
        self._show_view("dashboard")

        # Barra de estado
        self.statusbar = ttk.Label(
            self, text="Listo", anchor=W, style="info.TLabel")
        self.statusbar.pack(side=BOTTOM, fill=X)

    def _build_sidebar(self):
        nav_items = [
            ("Dashboard", "dashboard"),
            ("Bases de datos", "databases"),
            ("Historial", "history"),
            ("Programador", "scheduler"),
            ("Configuración", "settings"),
            ("Logs", "logs"),
        ]
        for text, key in nav_items:
            btn = ttk.Button(self.sidebar, text=text, command=lambda k=key: self._show_view(
                k), style="secondary.TButton")
            btn.pack(fill=X, pady=2, padx=8)

    def _clear_main_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def _show_view(self, view_key):
        self._clear_main_content()
        if view_key == "dashboard":
            self.current_view = DashboardView(self.main_content)
        elif view_key == "databases":
            self.current_view = DatabaseConfigView(self.main_content)
        elif view_key == "history":
            self.current_view = BackupHistoryView(self.main_content)
        elif view_key == "scheduler":
            self.current_view = BackupSchedulerView(self.main_content)
        elif view_key == "settings":
            self.current_view = SettingsView(self.main_content)
        elif view_key == "logs":
            self.current_view = LogsViewerView(self.main_content)
        else:
            self.current_view = ttk.Label(
                self.main_content, text="Vista no encontrada", font=("Segoe UI", 14))
        self.current_view.pack(fill=BOTH, expand=YES)

    def toggle_theme(self):
        # Cambia entre tema oscuro y claro
        if self.theme == "darkly":
            self.theme = "flatly"
        else:
            self.theme = "darkly"
        self.master.style.theme_use(self.theme)
