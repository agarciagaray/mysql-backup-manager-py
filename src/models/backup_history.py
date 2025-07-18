"""
Modelo de datos para el historial de respaldos
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from ..utils.helpers import parse_iso_datetime, format_bytes, format_duration

class BackupStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackupHistory:
    def __init__(self,
                 id: Optional[int] = None,
                 config_id: int = 0,
                 config_name: str = "",
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 status: str = "running",
                 message: Optional[str] = None,
                 file_path: Optional[str] = None,
                 file_size: Optional[int] = None,
                 duration_seconds: Optional[float] = None,
                 log_output: Optional[str] = None,
                 is_manual: bool = False):
        self.id = id
        self.config_id = config_id
        self.config_name = config_name
        self.start_time = start_time if start_time else datetime.now()
        self.end_time = end_time
        self.status = status
        self.message = message
        self.file_path = file_path
        self.file_size = file_size
        self.duration_seconds = duration_seconds
        self.log_output = log_output
        self.is_manual = is_manual

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto BackupHistory a un diccionario."""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "config_name": self.config_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "message": self.message,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "duration_seconds": self.duration_seconds,
            "log_output": self.log_output,
            "is_manual": int(self.is_manual)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupHistory":
        """Crea un objeto BackupHistory desde un diccionario."""
        return cls(
            id=data.get("id"),
            config_id=data.get("config_id", 0),
            config_name=data.get("config_name", ""),
            start_time=parse_iso_datetime(data.get("start_time")),
            end_time=parse_iso_datetime(data.get("end_time")),
            status=data.get("status", "running"),
            message=data.get("message"),
            file_path=data.get("file_path"),
            file_size=data.get("file_size"),
            duration_seconds=data.get("duration_seconds"),
            log_output=data.get("log_output"),
            is_manual=bool(data.get("is_manual", False))
        )
    
    def __repr__(self):
        return f"<BackupHistory(id={self.id}, config_name='{self.config_name}', status='{self.status}')>"
    
    @property
    def duration_formatted(self) -> str:
        """Retorna la duración formateada"""
        return format_duration(self.duration_seconds)
    
    @property
    def file_size_formatted(self) -> str:
        """Retorna el tamaño del archivo formateado"""
        return format_bytes(self.file_size)
    
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        return self.status == "failed"
    
    @property
    def is_running(self) -> bool:
        return self.status == "running"
