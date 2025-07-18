import logging
import os
import sys
import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from src.utils.constants import APP_DATA_DIR_NAME, LOG_FILE_NAME
from src.utils.helpers import (copy_assets_to_app_data, get_app_data_path,
                               setup_logging)
from src.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def main():
    setup_logging()
    logger.info("Iniciando aplicación...")
    copy_assets_to_app_data()

    app = tb.Window(themename="darkly")  # Tema moderno por defecto
    app.title("MySQL Backup Manager")
    app.geometry("1200x800")
    app.resizable(True, True)

    main_window = MainWindow(app)
    main_window.pack(fill=BOTH, expand=YES)

    logger.info("Aplicación iniciada.")
    app.mainloop()
    logger.info("Aplicación cerrada.")
    sys.exit(0)


if __name__ == "__main__":
    main()
