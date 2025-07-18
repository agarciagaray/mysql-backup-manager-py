import os
import sys
import platform
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Any

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon

from .constants import APP_DATA_DIR_NAME, LOG_FILE_NAME, LOG_FORMAT, LOG_DATE_FORMAT, APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)

def get_app_data_path(filename: str = "") -> str:
    """
    Retorna la ruta completa a un archivo dentro del directorio de datos de la aplicación,
    creando el directorio si no existe.
    """
    if platform.system() == "Windows":
        app_data_dir = os.path.join(os.environ.get("LOCALAPPDATA"), APP_DATA_DIR_NAME)
    elif platform.system() == "Darwin":  # macOS
        app_data_dir = os.path.join(os.path.expanduser("~/Library/Application Support"), APP_DATA_DIR_NAME)
    else:  # Linux y otros Unix-like
        app_data_dir = os.path.join(os.path.expanduser("~/.local/share"), APP_DATA_DIR_NAME)

    os.makedirs(app_data_dir, exist_ok=True)
    full_path = os.path.join(app_data_dir, filename)
    logger.debug(f"Ruta de datos de la aplicación: {full_path}")
    return full_path

def get_mysqldump_default_path() -> str:
    """
    Intenta determinar la ruta predeterminada de mysqldump según el sistema operativo.
    """
    if platform.system() == "Windows":
        # Rutas comunes para MySQL en Windows
        paths = [
            os.path.join(os.environ.get("ProgramFiles", ""), "MySQL", "MySQL Server 8.0", "bin", "mysqldump.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "MySQL", "MySQL Server 5.7", "bin", "mysqldump.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "MySQL", "MySQL Server 8.0", "bin", "mysqldump.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "MySQL", "MySQL Server 5.7", "bin", "mysqldump.exe"),
        ]
        for path in paths:
            if os.path.exists(path) and os.path.isfile(path):
                return path
        return "C:\\Program Files\\MySQL\\MySQL Server\\bin\\mysqldump.exe" # Ruta por defecto si no se encuentra
    elif platform.system() == "Darwin":  # macOS
        return "/usr/local/bin/mysqldump"
    else:  # Linux
        return "/usr/bin/mysqldump"

def show_message_box(title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Information,
                     buttons: QMessageBox.StandardButtons = QMessageBox.Ok, default_button: QMessageBox.StandardButton = QMessageBox.NoButton) -> QMessageBox.StandardButton:
    """Muestra un cuadro de diálogo de mensaje."""
    msg_box = QMessageBox()
    msg_box.setIcon(icon)
    msg_box.setText(message)
    msg_box.setWindowTitle(title)
    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)
    return msg_box.exec_()

def format_bytes(bytes_value: int) -> str:
    """Formatea un número de bytes a una cadena legible (KB, MB, GB)."""
    if bytes_value is None:
        return "N/A"
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / (1024**2):.2f} MB"
    else:
        return f"{bytes_value / (1024**3):.2f} GB"

def format_duration(seconds: Optional[float]) -> str:
    """Formatea una duración en segundos a una cadena legible (HH:MM:SS)."""
    if seconds is None:
        return "N/A"
    
    seconds = int(seconds)
    if seconds < 0:
        return "N/A" # O manejar como error/pasado
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{remaining_seconds:02}"

def format_timedelta(td: timedelta) -> str:
    """Devuelve una representación legible de un timedelta."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def setup_logging():
    """Configura el sistema de logging de la aplicación."""
    log_file_path = get_app_data_path(LOG_FILE_NAME)
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Nivel mínimo para capturar todo

    # Eliminar handlers existentes para evitar duplicados si se llama varias veces
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Mostrar INFO y superior en consola
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Handler para archivo
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG) # Guardar todo en el archivo
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    logger.info(f"Logging configurado. Los logs se guardan en: {log_file_path}")

def get_current_timestamp() -> str:
    """Retorna la fecha y hora actual en formato ISO para la base de datos."""
    return datetime.now().isoformat()

def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parsea una cadena de fecha y hora ISO a un objeto datetime."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        logger.error(f"Error al parsear fecha ISO: {dt_str}")
        return None

def to_json_string(data: List[Any]) -> str:
    """Convierte una lista a una cadena JSON."""
    return json.dumps(data)

def from_json_string(json_str: Optional[str]) -> List[Any]:
    """Convierte una cadena JSON a una lista. Retorna una lista vacía si la cadena es None o inválida."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning(f"Error al decodificar JSON: {json_str}. Retornando lista vacía.")
        return []

def get_icon(icon_name: str) -> QIcon:
    """Carga un icono desde la carpeta de assets."""
    # Asume que los iconos están en la carpeta 'assets/icons' en la raíz del proyecto
    # y que se han copiado al directorio de datos de la aplicación.
    icon_path = get_app_data_path(os.path.join("icons", f"{icon_name}.png"))
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    else:
        logger.warning(f"Icono no encontrado: {icon_path}. Usando icono predeterminado.")
        return QIcon() # Retorna un icono vacío si no se encuentra

def copy_assets_to_app_data():
    """Copia los assets (ej. iconos) al directorio de datos de la aplicación."""
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_source_dir = os.path.join(current_script_dir, '..', '..', 'assets', 'icons')
    assets_dest_dir = get_app_data_path("icons")

    if not os.path.exists(assets_source_dir):
        logger.warning(f"Directorio de assets no encontrado: {assets_source_dir}")
        return

    os.makedirs(assets_dest_dir, exist_ok=True)

    for item_name in os.listdir(assets_source_dir):
        source_item = os.path.join(assets_source_dir, item_name)
        dest_item = os.path.join(assets_dest_dir, item_name)
        if os.path.isfile(source_item):
            try:
                if not os.path.exists(dest_item) or os.path.getmtime(source_item) > os.path.getmtime(dest_item):
                    import shutil
                    shutil.copy2(source_item, dest_item)
                    logger.debug(f"Copiado/Actualizado asset: {item_name}")
            except Exception as e:
                logger.error(f"Error al copiar asset {item_name}: {e}")
