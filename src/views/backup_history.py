import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import *


class BackupHistoryView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text="Historial de Backups",
                          font=("Segoe UI", 18, "bold"))
        title.pack(anchor=W, pady=(10, 20), padx=20)

        # Filtros
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=X, padx=20)
        ttk.Label(filter_frame, text="Buscar:").pack(side=LEFT, padx=5)
        ttk.Entry(filter_frame).pack(side=LEFT, padx=5)
        ttk.Button(filter_frame, text="Filtrar",
                   bootstyle=INFO).pack(side=LEFT, padx=5)

        # Tabla de historial
        table = ttk.Treeview(self, columns=(
            "Fecha", "Base de datos", "Estado", "Archivo"), show="headings")
        for col in ("Fecha", "Base de datos", "Estado", "Archivo"):
            table.heading(col, text=col)
            table.column(col, width=120)
        table.pack(fill=BOTH, expand=YES, padx=20, pady=10)
