import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import *


class BackupSchedulerView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text="Programador de Backups",
                          font=("Segoe UI", 18, "bold"))
        title.pack(anchor=W, pady=(10, 20), padx=20)

        # Lista de tareas programadas
        table = ttk.Treeview(self, columns=(
            "Tarea", "Base de datos", "Frecuencia", "Próxima ejecución"), show="headings")
        for col in ("Tarea", "Base de datos", "Frecuencia", "Próxima ejecución"):
            table.heading(col, text=col)
            table.column(col, width=120)
        table.pack(fill=X, padx=20, pady=10)

        # Formulario básico
        form = ttk.LabelFrame(self, text="Nueva Programación")
        form.pack(fill=X, padx=20, pady=20)
        ttk.Label(form, text="Base de datos:").grid(
            row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form, text="Frecuencia:").grid(
            row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(form, text="Agregar", bootstyle=SUCCESS).grid(
            row=2, column=0, columnspan=2, pady=10)
