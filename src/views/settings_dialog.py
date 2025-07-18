import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import *


class SettingsView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text="Configuración",
                          font=("Segoe UI", 18, "bold"))
        title.pack(anchor=W, pady=(10, 20), padx=20)

        form = ttk.LabelFrame(self, text="Ajustes Generales")
        form.pack(fill=X, padx=20, pady=20)
        ttk.Label(form, text="Ruta de backups:").grid(
            row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form, text="Retención de backups (días):").grid(
            row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(form, text="Guardar", bootstyle=SUCCESS).grid(
            row=2, column=0, columnspan=2, pady=10)
