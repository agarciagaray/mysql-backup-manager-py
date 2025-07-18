import os
import sys
import logging

# Añadir el directorio raíz del proyecto al PYTHONPATH
# Esto permite importar módulos de src/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from src.models.database import database
from src.services.encryption_service import encryption_service
from src.repositories.app_settings_repository import app_settings_repository
from src.utils.helpers import setup_logging, get_app_data_path
from src.utils.constants import DB_FILE, ENCRYPTION_KEY_FILE

# Configurar logging para este script
setup_logging()
logger = logging.getLogger(__name__)

def initialize_database():
    """
    Inicializa la base de datos SQLite y asegura la existencia de la clave de encriptación.
    """
    logger.info("Iniciando la inicialización de la base de datos...")
    
    try:
        # La conexión a la base de datos y la inicialización del esquema
        # se manejan automáticamente al instanciar `database`
        # y al llamar a `_connect` y `_initialize_schema` en su constructor.
        # Solo necesitamos asegurarnos de que la instancia global esté accesible.
        _ = database 
        logger.info(f"Base de datos '{get_app_data_path(DB_FILE)}' verificada/creada.")

        # Asegurar que la clave de encriptación exista
        _ = encryption_service
        logger.info(f"Clave de encriptación '{get_app_data_path(ENCRYPTION_KEY_FILE)}' verificada/creada.")

        # Asegurar que los ajustes por defecto existan
        _ = app_settings_repository
        logger.info("Ajustes de aplicación por defecto verificados/creados.")

        logger.info("Base de datos y servicios iniciales configurados exitosamente.")
        print("\n¡Base de datos y servicios iniciales configurados exitosamente!")
        print(f"La base de datos se encuentra en: {get_app_data_path(DB_FILE)}")
        print(f"La clave de encriptación se encuentra en: {get_app_data_path(ENCRYPTION_KEY_FILE)}")
        print(f"Los logs se guardan en: {get_app_data_path('app.log')}")

    except Exception as e:
        logger.critical(f"Error crítico durante la inicialización de la base de datos: {e}", exc_info=True)
        print(f"\n¡ERROR CRÍTICO durante la inicialización de la base de datos: {e}")
        print("Por favor, revise los logs para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    initialize_database()
