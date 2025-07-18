import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from typing import TYPE_CHECKING
import logging
from PyQt5.QtWidgets import QToolBar, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from ...utils.helpers import get_app_data_path

if TYPE_CHECKING:
    from ..main_window import MainWindow

logger = logging.getLogger(__name__)

class Toolbar(ttk_bs.Frame, QToolBar):
    export_triggered = pyqtSignal()
    import_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    about_triggered = pyqtSignal()

    def __init__(self, master, main_window: 'MainWindow', parent=None):
        ttk_bs.Frame.__init__(self, master, bootstyle=LIGHT)
        QToolBar.__init__(self, "Barra de Herramientas", parent)
        self.main_window = main_window
        self.setIconSize(Qt.QSize(24, 24))
        self._create_widgets()
        self._init_actions()
        logger.info("Barra de herramientas inicializada.")

    def _create_widgets(self):
        """Crea los botones de la barra de herramientas."""
        # Botón Dashboard
        ttk_bs.Button(
            self,
            text="Dashboard",
            command=lambda: self.main_window.notebook.select(0), # Seleccionar la primera pestaña
            bootstyle=(INFO, OUTLINE),
            image=self.main_window.get_tab_icon("dashboard"),
            compound=tk.LEFT
        ).pack(side=LEFT, padx=2, pady=2)

        # Botón Configuraciones DB
        ttk_bs.Button(
            self,
            text="Configuraciones DB",
            command=lambda: self.main_window.notebook.select(1), # Seleccionar la segunda pestaña
            bootstyle=(INFO, OUTLINE),
            image=self.main_window.get_tab_icon("database"),
            compound=tk.LEFT
        ).pack(side=LEFT, padx=2, pady=2)

        # Botón Programación
        ttk_bs.Button(
            self,
            text="Programación",
            command=lambda: self.main_window.notebook.select(2), # Seleccionar la tercera pestaña
            bootstyle=(INFO, OUTLINE),
            image=self.main_window.get_tab_icon("schedule"),
            compound=tk.LEFT
        ).pack(side=LEFT, padx=2, pady=2)

        # Botón Logs
        ttk_bs.Button(
            self,
            text="Logs",
            command=lambda: self.main_window.notebook.select(3), # Seleccionar la cuarta pestaña
            bootstyle=(INFO, OUTLINE),
            image=self.main_window.get_tab_icon("logs"),
            compound=tk.LEFT
        ).pack(side=LEFT, padx=2, pady=2)

        # Botón Ajustes
        ttk_bs.Button(
            self,
            text="Ajustes",
            command=lambda: self.main_window.notebook.select(4), # Seleccionar la quinta pestaña
            bootstyle=(INFO, OUTLINE),
            image=self.main_window.get_tab_icon("settings"),
            compound=tk.LEFT
        ).pack(side=LEFT, padx=2, pady=2)

        # Separador
        ttk_bs.Separator(self, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10, pady=5)

        # Botón Forzar Respaldo Ahora (ejemplo, podría abrir un diálogo de selección)
        ttk_bs.Button(
            self,
            text="⚡ Respaldo Ahora",
            command=self._force_backup_dialog,
            bootstyle=(PRIMARY, OUTLINE),
            image=self.main_window.get_tab_icon("schedule"), # Usar el mismo icono de schedule
            compound=tk.LEFT
        ).pack(side=LEFT, padx=2, pady=2)

        # Botón Salir
        ttk_bs.Button(
            self,
            text="Salir",
            command=self.main_window._on_closing,
            bootstyle=(DANGER, OUTLINE),
            image=self.main_window.get_tab_icon("settings"), # Usar el mismo icono de settings
            compound=tk.LEFT
        ).pack(side=RIGHT, padx=2, pady=2)

    def _init_actions(self):
        """Inicializa las acciones de la barra de herramientas."""
        # Acción de Exportar
        export_action = QAction(QIcon(get_app_data_path("icons/export.png")), "Exportar Datos", self)
        export_action.setToolTip("Exportar todas las configuraciones y programaciones a un archivo.")
        export_action.triggered.connect(self.export_triggered.emit)
        self.addAction(export_action)

        # Acción de Importar
        import_action = QAction(QIcon(get_app_data_path("icons/import.png")), "Importar Datos", self)
        import_action.setToolTip("Importar configuraciones y programaciones desde un archivo.")
        import_action.triggered.connect(self.import_triggered.emit)
        self.addAction(import_action)

        self.addSeparator()

        # Acción de Ajustes
        settings_action = QAction(QIcon(get_app_data_path("icons/settings.png")), "Ajustes", self)
        settings_action.setToolTip("Configurar los ajustes de la aplicación.")
        settings_action.triggered.connect(self.settings_triggered.emit)
        self.addAction(settings_action)

        # Acción de Acerca de
        about_action = QAction(QIcon(get_app_data_path("icons/info.png")), "Acerca de", self)
        about_action.setToolTip("Información sobre la aplicación.")
        about_action.triggered.connect(self.about_triggered.emit)
        self.addAction(about_action)

    def _force_backup_dialog(self):
        """Muestra un diálogo para seleccionar una configuración y forzar un respaldo."""
        from ..repositories.backup_config_repository import backup_config_repository
        from ..services.scheduler_service import scheduler_service
        from ..services.notification_service import notification_service

        configs = backup_config_repository.get_all()
        if not configs:
            notification_service.show_warning("Forzar Respaldo", "No hay configuraciones de base de datos para respaldar.")
            return

        dialog = tk.Toplevel(self.master)
        dialog.title("Forzar Respaldo Ahora")
        dialog.geometry("300x150")
        dialog.transient(self.master)
        dialog.grab_set()

        ttk_bs.Label(dialog, text="Seleccione una configuración:").pack(pady=10)

        config_names = [f"{c.name} (ID: {c.id})" for c in configs]
        selected_config_id = tk.IntVar()
        
        config_combobox = ttk_bs.Combobox(
            dialog,
            textvariable=selected_config_id,
            values=config_names,
            state="readonly",
            width=30
        )
        config_combobox.pack(pady=5)
        if configs:
            config_combobox.set(config_names[0])
            selected_config_id.set(configs[0].id)

        def on_confirm():
            selected_text = config_combobox.get()
            if not selected_text:
                notification_service.show_warning("Error", "Por favor, seleccione una configuración.")
                return
            
            try:
                # Extraer el ID de la configuración
                config_id = int(selected_text.split('(ID: ')[1][:-1])
                if scheduler_service.force_backup_now(config_id):
                    notification_service.show_info("Respaldo Manual", f"Respaldo manual iniciado para la configuración ID: {config_id}.")
                else:
                    notification_service.show_error("Error", f"No se pudo iniciar el respaldo manual para la configuración ID: {config_id}.")
            except Exception as e:
                notification_service.show_error("Error", f"Error al procesar la selección: {e}")
            finally:
                dialog.destroy()

        ttk_bs.Button(dialog, text="Iniciar Respaldo", command=on_confirm, bootstyle=PRIMARY).pack(pady=10)
        dialog.wait_window()
