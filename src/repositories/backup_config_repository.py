import sqlite3
import logging
from typing import List, Optional, Dict, Any

from ..models.database import database
from ..models.backup_config import BackupConfig
from ..services.encryption_service import encryption_service
from ..utils.helpers import get_current_timestamp, from_json_string, to_json_string

logger = logging.getLogger(__name__)

class BackupConfigRepository:
    def __init__(self):
        self.db = database
        self.encryption_service = encryption_service
        logger.info("Repositorio de configuraciones de respaldo inicializado.")

    def add(self, config: BackupConfig) -> Optional[BackupConfig]:
        """Agrega una nueva configuración de respaldo a la base de datos."""
        query = """
            INSERT INTO database_configs (
                name, host, port, username, password_encrypted, database_name,
                mysqldump_path, backup_path, excluded_tables, compression_method,
                retention_days_main, retention_days_segregated, is_active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Encriptar la contraseña antes de guardar
        encrypted_password = self.encryption_service.encrypt(config.password_encrypted)
        
        params = (
            config.name, config.host, config.port, config.username, encrypted_password,
            config.database_name, config.mysqldump_path, config.backup_path,
            to_json_string(config.excluded_tables), config.compression_method,
            config.retention_days_main, config.retention_days_segregated, int(config.is_active),
            get_current_timestamp(), get_current_timestamp()
        )
        row_count = self.db.execute_update(query, params)
        if row_count > 0:
            config.id = self.db.get_last_insert_rowid()
            logger.info(f"Configuración '{config.name}' añadida con ID: {config.id}")
            return config
        logger.error(f"Fallo al añadir configuración: {config.name}")
        return None

    def update(self, config: BackupConfig) -> bool:
        """Actualiza una configuración de respaldo existente."""
        if config.id is None:
            logger.error("No se puede actualizar la configuración: ID no proporcionado.")
            return False
        
        # Obtener la configuración existente para comparar la contraseña
        existing_config = self.get_by_id(config.id)
        if existing_config and existing_config.password_encrypted == config.password_encrypted:
            # La contraseña no ha cambiado (ya está encriptada o es la misma desencriptada)
            encrypted_password = config.password_encrypted
        else:
            # La contraseña ha cambiado o no estaba encriptada, encriptar el nuevo valor
            encrypted_password = self.encryption_service.encrypt(config.password_encrypted)

        query = """
            UPDATE database_configs SET
                name = ?, host = ?, port = ?, username = ?, password_encrypted = ?,
                database_name = ?, mysqldump_path = ?, backup_path = ?,
                excluded_tables = ?, compression_method = ?,
                retention_days_main = ?, retention_days_segregated = ?, is_active = ?,
                updated_at = ?
            WHERE id = ?
        """
        params = (
            config.name, config.host, config.port, config.username, encrypted_password,
            config.database_name, config.mysqldump_path, config.backup_path,
            to_json_string(config.excluded_tables), config.compression_method,
            config.retention_days_main, config.retention_days_segregated, int(config.is_active),
            get_current_timestamp(), config.id
        )
        success = self.db.execute_update(query, params) > 0
        if success:
            logger.info(f"Configuración '{config.name}' (ID: {config.id}) actualizada.")
        else:
            logger.error(f"Fallo al actualizar configuración: {config.name} (ID: {config.id})")
        return success

    def delete(self, config_id: int) -> bool:
        """Elimina una configuración de respaldo por su ID."""
        query = "DELETE FROM database_configs WHERE id = ?"
        success = self.db.execute_update(query, (config_id,)) > 0
        if success:
            logger.info(f"Configuración con ID: {config_id} eliminada.")
        else:
            logger.error(f"Fallo al eliminar configuración con ID: {config_id}")
        return success

    def get_by_id(self, config_id: int) -> Optional[BackupConfig]:
        """Obtiene una configuración de respaldo por su ID."""
        query = "SELECT * FROM database_configs WHERE id = ?"
        row = self.db.execute_query(query, (config_id,))
        if row:
            data = dict(row[0])
            # Desencriptar la contraseña al cargar
            if 'password_encrypted' in data and data['password_encrypted']:
                data['password_encrypted'] = self.encryption_service.decrypt(data['password_encrypted'])
            return BackupConfig.from_dict(data)
        return None

    def get_by_name(self, name: str) -> Optional[BackupConfig]:
        """Obtiene una configuración de respaldo por su nombre."""
        query = "SELECT * FROM database_configs WHERE name = ?"
        row = self.db.execute_query(query, (name,))
        if row:
            data = dict(row[0])
            # Desencriptar la contraseña al cargar
            if 'password_encrypted' in data and data['password_encrypted']:
                data['password_encrypted'] = self.encryption_service.decrypt(data['password_encrypted'])
            return BackupConfig.from_dict(data)
        return None

    def get_all(self) -> List[BackupConfig]:
        """Obtiene todas las configuraciones de respaldo."""
        query = "SELECT * FROM database_configs ORDER BY name ASC"
        rows = self.db.execute_query(query)
        configs = []
        for row in rows:
            data = dict(row)
            # Desencriptar la contraseña al cargar
            if 'password_encrypted' in data and data['password_encrypted']:
                data['password_encrypted'] = self.encryption_service.decrypt(data['password_encrypted'])
            configs.append(BackupConfig.from_dict(data))
        return configs

    def get_active(self) -> List[BackupConfig]:
        """Obtiene todas las configuraciones de respaldo activas."""
        query = "SELECT * FROM database_configs WHERE is_active = 1 ORDER BY name ASC"
        rows = self.db.execute_query(query)
        configs = []
        for row in rows:
            data = dict(row)
            # Desencriptar la contraseña al cargar
            if 'password_encrypted' in data and data['password_encrypted']:
                data['password_encrypted'] = self.encryption_service.decrypt(data['password_encrypted'])
            configs.append(BackupConfig.from_dict(data))
        return configs

# Instancia global del repositorio
backup_config_repository = BackupConfigRepository()
