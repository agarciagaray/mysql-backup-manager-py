from typing import List, Optional
from datetime import datetime
import json
import logging

from ..models.database import database
from ..models.backup_schedule import BackupSchedule
from ..utils.helpers import from_json_string, to_json_string, get_current_timestamp, parse_iso_datetime

logger = logging.getLogger(__name__)

class BackupScheduleRepository:
    def __init__(self):
        self.db = database
        logger.info("Repositorio de programaciones de respaldo inicializado.")

    def add(self, schedule: BackupSchedule) -> Optional[BackupSchedule]:
        """Agrega una nueva programación de respaldo a la base de datos."""
        query = """
            INSERT INTO backup_schedules (
                config_id, schedule_type, time, days_of_week, day_of_month, is_active,
                last_run_time, next_run_time, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            schedule.config_id, schedule.schedule_type, schedule.time,
            to_json_string(schedule.days_of_week) if schedule.days_of_week else None,
            schedule.day_of_month, int(schedule.is_active),
            schedule.last_run_time.isoformat() if schedule.last_run_time else None,
            schedule.next_run_time.isoformat() if schedule.next_run_time else None,
            get_current_timestamp(), get_current_timestamp()
        )
        row_count = self.db.execute_update(query, params)
        if row_count > 0:
            schedule.id = self.db.get_last_insert_rowid()
            logger.info(f"Programación añadida para config_id {schedule.config_id} con ID: {schedule.id}")
            return schedule
        logger.error(f"Fallo al añadir programación para config_id: {schedule.config_id}")
        return None

    def update(self, schedule: BackupSchedule) -> bool:
        """Actualiza una programación de respaldo existente."""
        if schedule.id is None:
            logger.error("No se puede actualizar la programación: ID no proporcionado.")
            return False
        query = """
            UPDATE backup_schedules SET
                config_id = ?, schedule_type = ?, time = ?, days_of_week = ?, day_of_month = ?,
                is_active = ?, last_run_time = ?, next_run_time = ?, updated_at = ?
            WHERE id = ?
        """
        params = (
            schedule.config_id, schedule.schedule_type, schedule.time,
            to_json_string(schedule.days_of_week) if schedule.days_of_week else None,
            schedule.day_of_month, int(schedule.is_active),
            schedule.last_run_time.isoformat() if schedule.last_run_time else None,
            schedule.next_run_time.isoformat() if schedule.next_run_time else None,
            get_current_timestamp(), schedule.id
        )
        success = self.db.execute_update(query, params) > 0
        if success:
            logger.info(f"Programación (ID: {schedule.id}) actualizada.")
        else:
            logger.error(f"Fallo al actualizar programación (ID: {schedule.id})")
        return success

    def delete(self, schedule_id: int) -> bool:
        """Elimina una programación de respaldo por su ID."""
        query = "DELETE FROM backup_schedules WHERE id = ?"
        success = self.db.execute_update(query, (schedule_id,)) > 0
        if success:
            logger.info(f"Programación con ID: {schedule_id} eliminada.")
        else:
            logger.error(f"Fallo al eliminar programación con ID: {schedule_id}")
        return success

    def get_by_id(self, schedule_id: int) -> Optional[BackupSchedule]:
        """Obtiene una programación de respaldo por su ID."""
        query = "SELECT * FROM backup_schedules WHERE id = ?"
        row = self.db.execute_query(query, (schedule_id,))
        if row:
            data = dict(row[0])
            # Convertir days_of_week de JSON string a list
            if 'days_of_week' in data and data['days_of_week']:
                data['days_of_week'] = from_json_string(data['days_of_week'])
            return BackupSchedule.from_dict(data)
        return None

    def get_all(self) -> List[BackupSchedule]:
        """Obtiene todas las programaciones de respaldo."""
        query = "SELECT * FROM backup_schedules ORDER BY created_at ASC"
        rows = self.db.execute_query(query)
        schedules = []
        for row in rows:
            data = dict(row)
            # Convertir days_of_week de JSON string a list
            if 'days_of_week' in data and data['days_of_week']:
                data['days_of_week'] = from_json_string(data['days_of_week'])
            schedules.append(BackupSchedule.from_dict(data))
        return schedules

    def get_active_schedules(self) -> List[BackupSchedule]:
        """Obtiene todas las programaciones de respaldo activas."""
        query = "SELECT * FROM backup_schedules WHERE is_active = 1 ORDER BY created_at ASC"
        rows = self.db.execute_query(query)
        schedules = []
        for row in rows:
            data = dict(row)
            if 'days_of_week' in data and data['days_of_week']:
                data['days_of_week'] = from_json_string(data['days_of_week'])
            schedules.append(BackupSchedule.from_dict(data))
        return schedules

    def get_by_config_id(self, config_id: int) -> Optional[BackupSchedule]:
        """Obtiene una programación de respaldo por el ID de configuración."""
        query = "SELECT * FROM backup_schedules WHERE config_id = ? LIMIT 1"
        row = self.db.execute_query(query, (config_id,))
        if row:
            data = dict(row[0])
            if 'days_of_week' in data and data['days_of_week']:
                data['days_of_week'] = from_json_string(data['days_of_week'])
            return BackupSchedule.from_dict(data)
        return None

# Instancia global del repositorio
backup_schedule_repository = BackupScheduleRepository()
