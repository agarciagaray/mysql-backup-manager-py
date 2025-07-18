import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QLabel, QLineEdit, QFormLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt

from ..utils.helpers import to_json_string, from_json_string, get_current_timestamp, parse_iso_datetime
from ..utils.validators import (
    is_valid_port, is_valid_path, is_valid_file_path,
    is_valid_retention_days, is_valid_host
)
from ..utils.constants import COMPRESSION_METHODS


class BackupConfig:
    def __init__(self,
        id: Optional[int] = None,
        name: str = "",
        host: str = "localhost",
        port: int = 3306,
        username: str = "root",
        password_encrypted: str = "",
        database_name: str = "",
        mysqldump_path: str = "",
        backup_path: str = "",
        excluded_tables: Optional[List[str]] = None,
        compression_method: str = "zip",
        retention_days_main: int = 7,
        retention_days_segregated: int = 30,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None):

        self.id = id
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password_encrypted = password_encrypted
        self.database_name = database_name
        self.mysqldump_path = mysqldump_path
        self.backup_path = backup_path
        self.excluded_tables = excluded_tables if excluded_tables is not None else []
        self.compression_method = compression_method.lower()
        self.retention_days_main = retention_days_main
        self.retention_days_segregated = retention_days_segregated
        self.is_active = is_active
        self.created_at = created_at if created_at else datetime.now()
        self.updated_at = updated_at if updated_at else datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto BackupConfig a un diccionario serializable."""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password_encrypted": self.password_encrypted,
            "database_name": self.database_name,
            "mysqldump_path": self.mysqldump_path,
            "backup_path": self.backup_path,
            "excluded_tables": to_json_string(self.excluded_tables),
            "compression_method": self.compression_method,
            "retention_days_main": self.retention_days_main,
            "retention_days_segregated": self.retention_days_segregated,
            "is_active": int(self.is_active),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupConfig":
        """Crea un objeto BackupConfig desde un diccionario."""
        # Manejo robusto de excluded_tables
        raw_excluded = data.get("excluded_tables", "[]")
        if isinstance(raw_excluded, list):
            excluded = raw_excluded
        else:
            try:
                excluded = from_json_string(raw_excluded) or []
            except Exception:
                excluded = []

        # Manejo robusto de fechas
        created = parse_iso_datetime(data.get("created_at")) or datetime.now()
        updated = parse_iso_datetime(data.get("updated_at")) or datetime.now()

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            host=data.get("host", "localhost"),
            port=data.get("port", 3306),
            username=data.get("username", "root"),
            password_encrypted=data.get("password_encrypted", ""),
            database_name=data.get("database_name", ""),
            mysqldump_path=data.get("mysqldump_path", ""),
            backup_path=data.get("backup_path", ""),
            excluded_tables=excluded,
            compression_method=data.get("compression_method", "zip"),
            retention_days_main=data.get("retention_days_main", 7),
            retention_days_segregated=data.get("retention_days_segregated", 30),
            is_active=bool(data.get("is_active", True)),
            created_at=created,
            updated_at=updated
        )

    def __repr__(self):
        return f"<BackupConfig(id={self.id}, name='{self.name}', database='{self.database_name}')>"

    def validate(self) -> Tuple[bool, str]:
        """Valida los campos de la configuración de respaldo."""
        logging.debug("Validando configuración de respaldo: %s", self.to_dict())

        if not self.name.strip():
            return False, "El nombre de la configuración no puede estar vacío."
        if not self.host.strip() or not is_valid_host(self.host):
            return False, "Host inválido."
        if not is_valid_port(str(self.port)):
            return False, "Puerto inválido (debe ser un número entre 1 y 65535)."
        if not self.username.strip():
            return False, "El nombre de usuario no puede estar vacío."
        if not self.database_name.strip():
            return False, "El nombre de la base de datos no puede estar vacío."
        if not self.mysqldump_path.strip() or not is_valid_file_path(self.mysqldump_path):
            return False, "Ruta de mysqldump inválida o el archivo no existe."
        if not self.backup_path.strip() or not is_valid_path(self.backup_path):
            return False, "Ruta de respaldo inválida o el directorio no existe."
        if self.compression_method.lower() not in [m.lower() for m in COMPRESSION_METHODS]:
            return False, "Método de compresión inválido."
        if not is_valid_retention_days(str(self.retention_days_main)):
            return False, "Días de retención principal inválidos (debe ser un número no negativo)."
        if not is_valid_retention_days(str(self.retention_days_segregated)):
            return False, "Días de retención segregados inválidos (debe ser un número no negativo)."

        return True, "Validación exitosa."
