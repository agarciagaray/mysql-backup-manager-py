from collections.abc import Mapping
from typing import Optional, Tuple, Any  # Añadimos Any a la importación
from datetime import datetime

# Requiere Python 3.5+
from ..utils.helpers import parse_iso_datetime
from ..utils.validators import is_valid_port, is_valid_retention_days, is_valid_email
from ..utils.constants import NOTIFICATION_LEVELS

class AppSettings:
    def __init__(self,
                 id: Optional[int] = None,
                 window_width: int = 1024,
                 window_height: int = 768,
                 window_maximized: bool = False,
                 auto_start_scheduler: bool = True,
                 notification_level: str = 'info',
                 log_retention_days: int = 30,
                 default_backup_path: Optional[str] = None,
                 default_mysqldump_path: Optional[str] = None,
                 email_notifications_enabled: bool = False,
                 email_recipient: Optional[str] = None,
                 email_smtp_server: Optional[str] = None,
                 email_smtp_port: Optional[int] = None,
                 email_username: Optional[str] = None,
                 email_password_encrypted: Optional[str] = None,
                 email_sender_name: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.window_width = window_width
        self.window_height = window_height
        self.window_maximized = window_maximized
        self.auto_start_scheduler = auto_start_scheduler
        self.notification_level = notification_level
        self.log_retention_days = log_retention_days
        self.default_backup_path = default_backup_path
        self.default_mysqldump_path = default_mysqldump_path
        self.email_notifications_enabled = email_notifications_enabled
        self.email_recipient = email_recipient
        self.email_smtp_server = email_smtp_server
        self.email_smtp_port = email_smtp_port
        self.email_username = email_username
        self.email_password_encrypted = email_password_encrypted
        self.email_sender_name = email_sender_name
        self.created_at = created_at if created_at else datetime.now()
        self.updated_at = updated_at if updated_at else datetime.now()

    def to_dict(self) -> Mapping[str, Any]:
        """Convierte el objeto AppSettings a un diccionario."""
        return {
            "id": self.id,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_maximized": int(self.window_maximized),
            "auto_start_scheduler": int(self.auto_start_scheduler),
            "notification_level": self.notification_level,
            "log_retention_days": self.log_retention_days,
            "default_backup_path": self.default_backup_path,
            "default_mysqldump_path": self.default_mysqldump_path,
            "email_notifications_enabled": int(self.email_notifications_enabled),
            "email_recipient": self.email_recipient,
            "email_smtp_server": self.email_smtp_server,
            "email_smtp_port": self.email_smtp_port,
            "email_username": self.email_username,
            "email_password_encrypted": self.email_password_encrypted,
            "email_sender_name": self.email_sender_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AppSettings":
        """Crea un objeto AppSettings desde un diccionario."""
        return cls(
            id=data.get("id"),
            window_width=data.get("window_width", 1024),
            window_height=data.get("window_height", 768),
            window_maximized=bool(data.get("window_maximized", False)),
            auto_start_scheduler=bool(data.get("auto_start_scheduler", True)),
            notification_level=data.get("notification_level", 'info'),
            log_retention_days=data.get("log_retention_days", 30),
            default_backup_path=data.get("default_backup_path"),
            default_mysqldump_path=data.get("default_mysqldump_path"),
            email_notifications_enabled=bool(data.get("email_notifications_enabled", False)),
            email_recipient=data.get("email_recipient"),
            email_smtp_server=data.get("email_smtp_server"),
            email_smtp_port=data.get("email_smtp_port"),
            email_username=data.get("email_username"),
            email_password_encrypted=data.get("email_password_encrypted"),
            email_sender_name=data.get("email_sender_name"),
            created_at=parse_iso_datetime(data.get("created_at")),
            updated_at=parse_iso_datetime(data.get("updated_at"))
        )

    def validate(self) -> Tuple[bool, str]:
        """Valida los campos de la configuración de la aplicación."""
        if self.notification_level not in NOTIFICATION_LEVELS:
            return False, "Nivel de notificación inválido."
        if not is_valid_retention_days(str(self.log_retention_days)):
            return False, "Días de retención de logs inválidos (debe ser un número no negativo)."
        
        if self.email_notifications_enabled:
            if not self.email_recipient or not is_valid_email(self.email_recipient):
                return False, "Destinatario de email inválido."
            if not self.email_smtp_server:
                return False, "Servidor SMTP de email no puede estar vacío."
            if not self.email_smtp_port or not is_valid_port(str(self.email_smtp_port)):
                return False, "Puerto SMTP de email inválido."
            if not self.email_username:
                return False, "Usuario de email no puede estar vacío."
            # password_encrypted puede estar vacío si no se ha configurado aún, pero no se valida aquí.
            # sender_name es opcional.
        
        return True, "Validación exitosa."