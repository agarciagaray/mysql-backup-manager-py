import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import *


class DatabaseConfigView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text="Bases de Datos",
                          font=("Segoe UI", 18, "bold"))
        title.pack(anchor=W, pady=(10, 20), padx=20)

        # Tabla de bases de datos
        table = ttk.Treeview(self, columns=(
            "Nombre", "Host", "Usuario"), show="headings")
        for col in ("Nombre", "Host", "Usuario"):
            table.heading(col, text=col)
            table.column(col, width=120)
        table.pack(fill=X, padx=20, pady=10)

        # Formulario básico
        form = ttk.LabelFrame(self, text="Agregar/Editar Base de Datos")
        form.pack(fill=X, padx=20, pady=20)
        ttk.Label(form, text="Nombre:").grid(
            row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form, text="Host:").grid(
            row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(form, text="Usuario:").grid(
            row=2, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(form).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(form, text="Guardar", bootstyle=SUCCESS).grid(
            row=3, column=0, columnspan=2, pady=10)
