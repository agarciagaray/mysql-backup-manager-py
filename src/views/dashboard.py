"""
Vista del Dashboard principal
"""
import logging
import os
import subprocess
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk
from typing import Callable, Optional

import ttkbootstrap as tb
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QScrollArea,
                             QVBoxLayout, QWidget)
from ttkbootstrap.constants import *

from ..repositories.backup_config_repository import backup_config_repository
from ..repositories.backup_history_repository import backup_history_repository
from ..services.backup_service import backup_service
from ..services.notification_service import notification_service
from ..services.scheduler_service import scheduler_service
from ..utils.constants import (BACKUP_STATUS_FAILED, BACKUP_STATUS_RUNNING,
                               BACKUP_STATUS_SUCCESS)
from ..utils.helpers import format_bytes, format_timedelta
from .components.backup_history_table import BackupHistoryTable
from .components.quick_actions import QuickActions
from .components.scheduler_status import SchedulerStatusWidget
from .components.statistics_cards import StatisticsCards

logger = logging.getLogger(__name__)


class DashboardView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        # Título
        title = ttk.Label(self, text="Dashboard",
                          font=("Segoe UI", 18, "bold"))
        title.pack(anchor=W, pady=(10, 20), padx=20)

        # Tarjetas de estadísticas
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=X, padx=20)
        for i, (label, value) in enumerate([
            ("Backups realizados", "0"),
            ("Errores", "0"),
                ("Espacio usado", "0 MB")]):
            card = tb.widgets.Meter(
                stats_frame,
                bootstyle=SUCCESS if i == 0 else DANGER if i == 1 else INFO,
                amountused=int(value.split()[0]),
                subtext=label,
                metertype='semi'
            )
            card.grid(row=0, column=i, padx=10, pady=10)

        # Estado del programador
        scheduler_frame = ttk.LabelFrame(self, text="Estado del Programador")
        scheduler_frame.pack(fill=X, padx=20, pady=20)
        status_lbl = ttk.Label(scheduler_frame, text="Activo", font=(
            "Segoe UI", 12), foreground="green")
        status_lbl.pack(anchor=W, padx=10, pady=10)
