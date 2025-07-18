import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.database import database
from ..models.backup_history import BackupHistory
from ..utils.helpers import get_current_timestamp, parse_iso_datetime
from ..utils.constants import BACKUP_STATUS_SUCCESS, BACKUP_STATUS_FAILED, BACKUP_STATUS_RUNNING

logger = logging.getLogger(__name__)

class BackupHistoryRepository:
    def __init__(self):
        self.db = database
        logger.info("Repositorio de historial de respaldos inicializado.")

    def add(self, history: BackupHistory) -> Optional[BackupHistory]:
        """Agrega un nuevo registro de historial de respaldo a la base de datos."""
        query = """
            INSERT INTO backup_history (
                config_id, config_name, start_time, end_time, status, message,
                file_path, file_size, duration_seconds, log_output, is_manual
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            history.config_id, history.config_name, history.start_time.isoformat(),
            history.end_time.isoformat() if history.end_time else None,
            history.status, history.message, history.file_path, history.file_size,
            history.duration_seconds, history.log_output, int(history.is_manual)
        )
        row_count = self.db.execute_update(query, params)
        if row_count > 0:
            history.id = self.db.get_last_insert_rowid()
            logger.info(f"Registro de historial añadido para config '{history.config_name}' con ID: {history.id}")
            return history
        logger.error(f"Fallo al añadir registro de historial para config: {history.config_name}")
        return None

    def update(self, history: BackupHistory) -> bool:
        """Actualiza un registro de historial de respaldo existente."""
        if history.id is None:
            logger.error("No se puede actualizar el historial: ID no proporcionado.")
            return False
        query = """
            UPDATE backup_history SET
                config_id = ?, config_name = ?, start_time = ?, end_time = ?, status = ?, message = ?,
                file_path = ?, file_size = ?, duration_seconds = ?, log_output = ?, is_manual = ?
            WHERE id = ?
        """
        params = (
            history.config_id, history.config_name, history.start_time.isoformat(),
            history.end_time.isoformat() if history.end_time else None,
            history.status, history.message, history.file_path, history.file_size,
            history.duration_seconds, history.log_output, int(history.is_manual),
            history.id
        )
        success = self.db.execute_update(query, params) > 0
        if success:
            logger.info(f"Registro de historial (ID: {history.id}) actualizado.")
        else:
            logger.error(f"Fallo al actualizar registro de historial (ID: {history.id})")
        return success

    def delete(self, history_id: int) -> bool:
        """Elimina un registro de historial de respaldo por su ID."""
        query = "DELETE FROM backup_history WHERE id = ?"
        success = self.db.execute_update(query, (history_id,)) > 0
        if success:
            logger.info(f"Registro de historial con ID: {history_id} eliminado.")
        else:
            logger.error(f"Fallo al eliminar registro de historial con ID: {history_id}")
        return success

    def get_by_id(self, history_id: int) -> Optional[BackupHistory]:
        """Obtiene un registro de historial de respaldo por su ID."""
        query = "SELECT * FROM backup_history WHERE id = ?"
        row = self.db.execute_query(query, (history_id,))
        if row:
            return BackupHistory.from_dict(dict(row[0]))
        return None

    def get_all(self) -> List[BackupHistory]:
        """Obtiene todos los registros de historial de respaldo, ordenados por fecha de inicio descendente."""
        query = "SELECT * FROM backup_history ORDER BY start_time DESC"
        rows = self.db.execute_query(query)
        return [BackupHistory.from_dict(dict(row)) for row in rows]

    def get_by_config_id(self, config_id: int, limit: int = 100) -> List[BackupHistory]:
        """Obtiene los registros de historial para una configuración específica."""
        query = "SELECT * FROM backup_history WHERE config_id = ? ORDER BY start_time DESC LIMIT ?"
        rows = self.db.execute_query(query, (config_id, limit))
        return [BackupHistory.from_dict(dict(row)) for row in rows]

    def get_total_backups(self) -> int:
        """Retorna el número total de respaldos (exitosos y fallidos)."""
        query = "SELECT COUNT(*) FROM backup_history WHERE status IN (?, ?)"
        result = self.db.execute_query(query, (BACKUP_STATUS_SUCCESS, BACKUP_STATUS_FAILED))
        return result[0][0] if result else 0

    def get_successful_backups(self) -> int:
        """Retorna el número de respaldos exitosos."""
        query = "SELECT COUNT(*) FROM backup_history WHERE status = ?"
        result = self.db.execute_query(query, (BACKUP_STATUS_SUCCESS,))
        return result[0][0] if result else 0

    def get_failed_backups(self) -> int:
        """Retorna el número de respaldos fallidos."""
        query = "SELECT COUNT(*) FROM backup_history WHERE status = ?"
        result = self.db.execute_query(query, (BACKUP_STATUS_FAILED,))
        return result[0][0] if result else 0

    def get_running_backups(self) -> int:
        """Retorna el número de respaldos actualmente en ejecución."""
        query = "SELECT COUNT(*) FROM backup_history WHERE status = ?"
        result = self.db.execute_query(query, (BACKUP_STATUS_RUNNING,))
        return result[0][0] if result else 0

    def get_last_backup_time(self) -> Optional[datetime]:
        """Retorna la fecha y hora del último respaldo exitoso."""
        query = "SELECT start_time FROM backup_history WHERE status = ? ORDER BY start_time DESC LIMIT 1"
        result = self.db.execute_query(query, (BACKUP_STATUS_SUCCESS,))
        if result and result[0][0]:
            return parse_iso_datetime(result[0][0])
        return None

    def get_total_backup_size(self) -> int:
        """Retorna el tamaño total en bytes de todos los respaldos exitosos."""
        query = "SELECT SUM(file_size) FROM backup_history WHERE status = ? AND file_size IS NOT NULL"
        result = self.db.execute_query(query, (BACKUP_STATUS_SUCCESS,))
        return result[0][0] if result and result[0][0] is not None else 0

    def delete_old_logs(self, retention_days: int):
        """Elimina registros de historial más antiguos que los días de retención especificados."""
        if retention_days < 0:
            logger.warning("Días de retención negativos, no se eliminarán logs.")
            return
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        query = "DELETE FROM backup_history WHERE start_time < ?"
        params = (cutoff_date.isoformat(),)
        deleted_count = self.db.execute_update(query, params)
        logger.info(f"Eliminados {deleted_count} registros de historial más antiguos que {retention_days} días.")

# Instancia global del repositorio
backup_history_repository = BackupHistoryRepository()
