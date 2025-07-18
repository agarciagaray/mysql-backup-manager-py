import sqlite3
import logging
import os
from typing import List, Tuple, Any, Optional, Dict

from ..utils.helpers import get_app_data_path
from ..utils.constants import DB_FILE, DB_SCHEMA

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = get_app_data_path(DB_FILE)
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._connect()
        self._initialize_schema()
        logger.info(f"Base de datos inicializada en: {self.db_path}")

    def _connect(self):
        """Establece la conexión a la base de datos."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Para acceder a las columnas por nombre
            self.cursor = self.conn.cursor()
            logger.debug("Conexión a la base de datos establecida.")
        except sqlite3.Error as e:
            logger.critical(f"Error al conectar a la base de datos: {e}")
            raise

    def _initialize_schema(self):
        """Crea las tablas si no existen."""
        try:
            self.cursor.executescript(DB_SCHEMA)
            self.conn.commit()
            logger.info("Esquema de la base de datos verificado/creado.")
        except sqlite3.Error as e:
            logger.critical(f"Error al inicializar el esquema de la base de datos: {e}")
            raise

    def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        """Ejecuta una consulta SELECT y retorna los resultados."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error al ejecutar consulta: {query} con params {params}. Error: {e}")
            return []

    def execute_update(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """Ejecuta una consulta INSERT, UPDATE o DELETE y retorna el número de filas afectadas."""
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error al ejecutar actualización: {query} con params {params}. Error: {e}")
            self.conn.rollback()
            return -1

    def get_last_insert_rowid(self) -> Optional[int]:
        """Retorna el ID de la última fila insertada."""
        if self.cursor:
            return self.cursor.lastrowid
        return None

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            logger.debug("Conexión a la base de datos cerrada.")

    def backup_database(self, backup_path: str):
        """Crea una copia de seguridad de la base de datos actual."""
        try:
            # Cerrar la conexión actual para asegurar que el archivo no esté bloqueado
            self.close()
            
            # Copiar el archivo de la base de datos
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Copia de seguridad de la base de datos creada en: {backup_path}")
            
            # Volver a conectar
            self._connect()
        except Exception as e:
            logger.error(f"Error al crear copia de seguridad de la base de datos: {e}")
            # Intentar reconectar incluso si falla la copia
            self._connect()
            raise

    def restore_database(self, restore_path: str) -> bool:
        """Restaura la base de datos desde un archivo de copia de seguridad."""
        try:
            if not os.path.exists(restore_path):
                logger.error(f"Archivo de respaldo para restaurar no encontrado: {restore_path}")
                return False
            
            # Cerrar la conexión actual
            self.close()
            
            # Reemplazar el archivo de la base de datos actual con el de respaldo
            import shutil
            shutil.copy2(restore_path, self.db_path)
            logger.info(f"Base de datos restaurada desde: {restore_path}")
            
            # Volver a conectar
            self._connect()
            return True
        except Exception as e:
            logger.error(f"Error al restaurar la base de datos: {e}")
            # Intentar reconectar incluso si falla la restauración
            self._connect()
            return False

# Instancia global de la base de datos
database = Database()
