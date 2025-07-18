import sqlite3
import logging
from typing import Optional, Dict, Any

from ..models.database import database
from ..models.app_settings import AppSettings
from ..services.encryption_service import encryption_service
from ..utils.helpers import get_current_timestamp, parse_iso_datetime

logger = logging.getLogger(__name__)

class AppSettingsRepository:
    def __init__(self):
        self.db = database
        self.encryption_service = encryption_service
        self._ensure_default_settings()
        logger.info("Repositorio de ajustes de aplicación inicializado.")

    def _ensure_default_settings(self):
        """Asegura que siempre exista una entrada de ajustes por defecto."""
        settings = self.get_settings()
        if settings is None:
            default_settings = AppSettings()
            self._insert_settings(default_settings)
            logger.info("Ajustes por defecto insertados.")

    def _insert_settings(self, settings: AppSettings) -> Optional[AppSettings]:
        """Inserta una nueva fila de ajustes."""
        query = """
            INSERT INTO app_settings (
                window_width, window_height, window_maximized, auto_start_scheduler,
                notification_level, log_retention_days, default_backup_path,
                default_mysqldump_path, email_notifications_enabled, email_recipient,
                email_smtp_server, email_smtp_port, email_username,
                email_password_encrypted, email_sender_name, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        encrypted_password = self.encryption_service.encrypt(settings.email_password_encrypted) if settings.email_password_encrypted else None
        
        params = (
            settings.window_width, settings.window_height, int(settings.window_maximized),
            int(settings.auto_start_scheduler), settings.notification_level,
            settings.log_retention_days, settings.default_backup_path,
            settings.default_mysqldump_path, int(settings.email_notifications_enabled),
            settings.email_recipient, settings.email_smtp_server, settings.email_smtp_port,
            settings.email_username, encrypted_password, settings.email_sender_name,
            get_current_timestamp(), get_current_timestamp()
        )
        row_count = self.db.execute_update(query, params)
        if row_count > 0:
            settings.id = self.db.get_last_insert_rowid()
            return settings
        logger.error("Fallo al insertar ajustes.")
        return None

    def get_settings(self) -> Optional[AppSettings]:
        """Obtiene la única fila de ajustes de la aplicación."""
        query = "SELECT * FROM app_settings LIMIT 1"
        row = self.db.execute_query(query)
        if row:
            data = dict(row[0])
            # Desencriptar la contraseña al cargar
            if 'email_password_encrypted' in data and data['email_password_encrypted']:
                data['email_password_encrypted'] = self.encryption_service.decrypt(data['email_password_encrypted'])
            return AppSettings.from_dict(data)
        return None

    def save_settings(self, settings: AppSettings) -> bool:
        """Guarda los ajustes de la aplicación (actualiza la fila existente o inserta si no hay)."""
        if settings.id is None:
            # Si no tiene ID, intentar obtenerlo o insertar
            existing_settings = self.get_settings()
            if existing_settings:
                settings.id = existing_settings.id
            else:
                return self._insert_settings(settings) is not None

        # Encriptar la contraseña solo si ha cambiado o no estaba encriptada
        existing_settings = self.get_settings() # Obtener para comparar la contraseña
        encrypted_password = settings.email_password_encrypted
        if existing_settings and existing_settings.email_password_encrypted != settings.email_password_encrypted:
            # Si el valor desencriptado es diferente, encriptar el nuevo valor
            encrypted_password = self.encryption_service.encrypt(settings.email_password_encrypted)
        elif existing_settings:
            # Si el valor es el mismo, usar el ya encriptado de la DB
            encrypted_password = existing_settings.email_password_encrypted
        
        query = """
            UPDATE app_settings SET
                window_width = ?, window_height = ?, window_maximized = ?, auto_start_scheduler = ?,
                notification_level = ?, log_retention_days = ?, default_backup_path = ?,
                default_mysqldump_path = ?, email_notifications_enabled = ?, email_recipient = ?,
                email_smtp_server = ?, email_smtp_port = ?, email_username = ?,
                email_password_encrypted = ?, email_sender_name = ?, updated_at = ?
            WHERE id = ?
        """
        params = (
            settings.window_width, settings.window_height, int(settings.window_maximized),
            int(settings.auto_start_scheduler), settings.notification_level,
            settings.log_retention_days, settings.default_backup_path,
            settings.default_mysqldump_path, int(settings.email_notifications_enabled),
            settings.email_recipient, settings.email_smtp_server, settings.email_smtp_port,
            settings.email_username, encrypted_password, settings.email_sender_name,
            get_current_timestamp(), settings.id
        )
        success = self.db.execute_update(query, params) > 0
        if success:
            logger.info("Ajustes de aplicación guardados.")
        else:
            logger.error("Fallo al guardar ajustes de aplicación.")
        return success

# Instancia global del repositorio
app_settings_repository = AppSettingsRepository()
