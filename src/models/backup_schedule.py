from typing import Optional, List, Dict, Any, Tuple  # Añadimos Tuple a la importación
from datetime import datetime

from ..utils.helpers import parse_iso_datetime
from ..utils.validators import is_valid_time_format, is_valid_days_of_week, is_valid_day_of_month
from ..utils.constants import SCHEDULE_TYPES, SCHEDULE_TYPE_DAILY, SCHEDULE_TYPE_WEEKLY, SCHEDULE_TYPE_MONTHLY

class BackupSchedule:
    def __init__(self,
                 id: Optional[int] = None,
                 config_id: int = 0,
                 schedule_type: str = "daily", # 'daily', 'weekly', 'monthly'
                 time: str = "00:00", # HH:MM
                 days_of_week: Optional[List[int]] = None, # [0, 1, ..., 6] for weekly (0=Sunday)
                 day_of_month: Optional[int] = None, # 1-31 for monthly
                 is_active: bool = True,
                 last_run_time: Optional[datetime] = None,
                 next_run_time: Optional[datetime] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.config_id = config_id
        self.schedule_type = schedule_type
        self.time = time
        self.days_of_week = days_of_week if days_of_week is not None else []
        self.day_of_month = day_of_month
        self.is_active = is_active
        self.last_run_time = last_run_time
        self.next_run_time = next_run_time
        self.created_at = created_at if created_at else datetime.now()
        self.updated_at = updated_at if updated_at else datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto BackupSchedule a un diccionario."""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "schedule_type": self.schedule_type,
            "time": self.time,
            "days_of_week": self.days_of_week, # Se asume que ya es una lista, se serializará a JSON en el repo
            "day_of_month": self.day_of_month,
            "is_active": int(self.is_active),
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupSchedule":
        """Crea un objeto BackupSchedule desde un diccionario."""
        return cls(
            id=data.get("id"),
            config_id=data.get("config_id", 0),
            schedule_type=data.get("schedule_type", "daily"),
            time=data.get("time", "00:00"),
            days_of_week=data.get("days_of_week"), # Asumimos que ya viene como lista o None
            day_of_month=data.get("day_of_month"),
            is_active=bool(data.get("is_active", True)),
            last_run_time=parse_iso_datetime(data.get("last_run_time")),
            next_run_time=parse_iso_datetime(data.get("next_run_time")),
            created_at=parse_iso_datetime(data.get("created_at")),
            updated_at=parse_iso_datetime(data.get("updated_at"))
        )
    
    def __repr__(self):
        return f"<BackupSchedule(id={self.id}, config_id={self.config_id}, type='{self.schedule_type}', time='{self.time}')>"

    def validate(self) -> Tuple[bool, str]:
        """Valida los campos de la programación de respaldo."""
        if self.config_id <= 0:
            return False, "Debe seleccionar una configuración de base de datos."
        if self.schedule_type not in SCHEDULE_TYPES:
            return False, "Tipo de programación inválido."
        if not is_valid_time_format(self.time):
            return False, "Formato de hora inválido (HH:MM)."
        
        if self.schedule_type == SCHEDULE_TYPE_WEEKLY:
            if not self.days_of_week or not is_valid_days_of_week(self.days_of_week):
                return False, "Debe seleccionar al menos un día de la semana para la programación semanal."
        elif self.schedule_type == SCHEDULE_TYPE_MONTHLY:
            if not self.day_of_month or not is_valid_day_of_month(str(self.day_of_month)):
                return False, "Debe especificar un día del mes (1-31) para la programación mensual."
        
        return True, "Validación exitosa."