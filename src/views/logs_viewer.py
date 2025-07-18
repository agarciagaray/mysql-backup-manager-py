import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import *


class LogsViewerView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text="Logs de la Aplicación",
                          font=("Segoe UI", 18, "bold"))
        title.pack(anchor=W, pady=(10, 20), padx=20)

        # Filtro
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=X, padx=20)
        ttk.Label(filter_frame, text="Buscar:").pack(side=LEFT, padx=5)
        ttk.Entry(filter_frame).pack(side=LEFT, padx=5)
        ttk.Button(filter_frame, text="Filtrar",
                   bootstyle=INFO).pack(side=LEFT, padx=5)

        # Visor de logs
        log_text = tk.Text(self, height=20, wrap="none")
        log_text.pack(fill=BOTH, expand=YES, padx=20, pady=10)
        log_text.insert(END, "Aquí aparecerán los logs de la aplicación...")
