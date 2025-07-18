import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from typing import List, Optional, Dict, Any

from PyQt5.QtCore import pyqtSignal, QObject

from ..repositories.backup_schedule_repository import backup_schedule_repository
from ..repositories.backup_config_repository import backup_config_repository
from ..services.backup_service import backup_service
from ..models.backup_schedule import BackupSchedule
from ..utils.constants import SCHEDULE_TYPE_DAILY, SCHEDULE_TYPE_WEEKLY, SCHEDULE_TYPE_MONTHLY, DAYS_OF_WEEK
from ..utils.helpers import parse_iso_datetime

logger = logging.getLogger(__name__)

class SchedulerService(QObject):
    # Señal para notificar cambios en el estado del scheduler (ej. iniciado/detenido)
    scheduler_status_changed = pyqtSignal(bool)
    # Señal para notificar que un respaldo ha sido ejecutado (para refrescar UI)
    backup_executed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.scheduler = BackgroundScheduler()
        self.schedule_repo = backup_schedule_repository
        self.config_repo = backup_config_repository
        self.backup_service = backup_service
        self._is_running = False
        logger.info("Servicio de scheduler inicializado.")

    def start_scheduler(self):
        """Inicia el scheduler y carga las programaciones activas."""
        if not self._is_running:
            try:
                self.scheduler.start()
                self._is_running = True
                self.load_schedules()
                self.scheduler_status_changed.emit(True)
                logger.info("Scheduler iniciado.")
            except Exception as e:
                logger.error(f"Error al iniciar el scheduler: {e}")
        else:
            logger.info("El scheduler ya está en ejecución.")

    def shutdown_scheduler(self):
        """Detiene el scheduler."""
        if self._is_running:
            try:
                self.scheduler.shutdown(wait=False) # No esperar a que terminen los trabajos
                self._is_running = False
                self.scheduler_status_changed.emit(False)
                logger.info("Scheduler detenido.")
            except Exception as e:
                logger.error(f"Error al detener el scheduler: {e}")
        else:
            logger.info("El scheduler no está en ejecución.")

    def is_running(self) -> bool:
        """Retorna si el scheduler está en ejecución."""
        return self._is_running

    def get_next_run_time(self) -> Optional[datetime]:
        """Retorna la hora de la próxima ejecución programada."""
        jobs = self.scheduler.get_jobs()
        if jobs:
            next_times = [job.next_run_time for job in jobs if job.next_run_time]
            if next_times:
                return min(next_times)
        return None

    def load_schedules(self):
        """Carga todas las programaciones activas de la base de datos al scheduler."""
        self.scheduler.remove_all_jobs() # Limpiar trabajos existentes
        active_schedules = self.schedule_repo.get_active_schedules()
        logger.info(f"Cargando {len(active_schedules)} programaciones activas...")
        for schedule_obj in active_schedules:
            self._add_job_to_scheduler(schedule_obj)
        logger.info("Programaciones cargadas.")

    def _add_job_to_scheduler(self, schedule_obj: BackupSchedule):
        """Añade un trabajo al scheduler basado en un objeto BackupSchedule."""
        config = self.config_repo.get_by_id(schedule_obj.config_id)
        if not config or not config.is_active:
            logger.warning(f"Configuración de respaldo (ID: {schedule_obj.config_id}) no encontrada o inactiva para la programación (ID: {schedule_obj.id}). No se añadirá el trabajo.")
            return

        job_id = f"backup_job_{schedule_obj.id}"
        hour, minute = map(int, schedule_obj.time.split(':'))
        
        trigger = None
        if schedule_obj.schedule_type == SCHEDULE_TYPE_DAILY:
            trigger = CronTrigger(hour=hour, minute=minute)
        elif schedule_obj.schedule_type == SCHEDULE_TYPE_WEEKLY:
            # days_of_week es una lista de enteros [0-6] (0=Domingo, 6=Sábado)
            day_strings = ','.join(map(str, schedule_obj.days_of_week))
            trigger = CronTrigger(day_of_week=day_strings, hour=hour, minute=minute)
        elif schedule_obj.schedule_type == SCHEDULE_TYPE_MONTHLY:
            trigger = CronTrigger(day=schedule_obj.day_of_month, hour=hour, minute=minute)
        
        if trigger:
            try:
                self.scheduler.add_job(
                    func=self._execute_backup_job,
                    trigger=trigger,
                    args=[config.id, schedule_obj.id], # Pasar config_id y schedule_id
                    id=job_id,
                    name=f"Respaldo {config.name} ({schedule_obj.schedule_type})",
                    replace_existing=True
                )
                # Actualizar next_run_time en la DB
                job = self.scheduler.get_job(job_id)
                if job and job.next_run_time:
                    schedule_obj.next_run_time = job.next_run_time
                    self.schedule_repo.update(schedule_obj)
                logger.info(f"Trabajo '{job_id}' añadido al scheduler. Próxima ejecución: {schedule_obj.next_run_time}")
            except Exception as e:
                logger.error(f"Error al añadir trabajo {job_id} al scheduler: {e}")
        else:
            logger.error(f"Tipo de programación desconocido para el ID {schedule_obj.id}: {schedule_obj.schedule_type}")

    def _execute_backup_job(self, config_id: int, schedule_id: int):
        """Función que se ejecuta cuando un trabajo programado se activa."""
        logger.info(f"Ejecutando trabajo programado para config_id: {config_id}, schedule_id: {schedule_id}")
        config = self.config_repo.get_by_id(config_id)
        schedule_obj = self.schedule_repo.get_by_id(schedule_id)

        if not config or not config.is_active:
            logger.warning(f"Configuración (ID: {config_id}) no encontrada o inactiva. No se realizará el respaldo.")
            return
        if not schedule_obj or not schedule_obj.is_active:
            logger.warning(f"Programación (ID: {schedule_id}) no encontrada o inactiva. No se realizará el respaldo.")
            return

        try:
            # Verificar si ya hay un respaldo en ejecución para esta configuración
            if self.backup_service.is_backup_running(config_id):
                logger.warning(f"Ya hay un respaldo en ejecución para {config.name}. Saltando ejecución programada.")
                return

            self.backup_service.start_backup(config, is_manual=False)
            # Actualizar last_run_time y recalcular next_run_time
            schedule_obj.last_run_time = datetime.now()
            job = self.scheduler.get_job(f"backup_job_{schedule_obj.id}")
            if job and job.next_run_time:
                schedule_obj.next_run_time = job.next_run_time
            self.schedule_repo.update(schedule_obj)
            logger.info(f"Respaldo programado para {config.name} completado.")
            self.backup_executed.emit() # Emitir señal para refrescar la UI
        except Exception as e:
            logger.error(f"Error al ejecutar respaldo programado para {config.name}: {e}")
            self.backup_executed.emit() # Emitir señal incluso si falla para refrescar la UI

    def add_schedule(self, schedule_obj: BackupSchedule) -> Optional[BackupSchedule]:
        """Añade una nueva programación y la carga al scheduler."""
        new_schedule = self.schedule_repo.add(schedule_obj)
        if new_schedule and self._is_running:
            self._add_job_to_scheduler(new_schedule)
        return new_schedule

    def update_schedule(self, schedule_obj: BackupSchedule) -> bool:
        """Actualiza una programación existente y la recarga en el scheduler."""
        success = self.schedule_repo.update(schedule_obj)
        if success and self._is_running:
            # Eliminar el trabajo antiguo y añadir el nuevo para actualizarlo
            job_id = f"backup_job_{schedule_obj.id}"
            try:
                self.scheduler.remove_job(job_id)
                logger.debug(f"Trabajo '{job_id}' removido para actualización.")
            except JobLookupError:
                logger.warning(f"Trabajo '{job_id}' no encontrado para remover (posiblemente no estaba cargado).")
            self._add_job_to_scheduler(schedule_obj)
        return success

    def delete_schedule(self, schedule_id: int) -> bool:
        """Elimina una programación y la remueve del scheduler."""
        success = self.schedule_repo.delete(schedule_id)
        if success and self._is_running:
            job_id = f"backup_job_{schedule_id}"
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Trabajo '{job_id}' removido del scheduler.")
            except JobLookupError:
                logger.warning(f"Trabajo '{job_id}' no encontrado para remover (ya eliminado o no cargado).")
        return success

    def pause_all_jobs(self):
        """Pausa todos los trabajos del scheduler."""
        if self._is_running:
            self.scheduler.pause()
            logger.info("Todos los trabajos del scheduler han sido pausados.")
            self.scheduler_status_changed.emit(True) # Sigue corriendo pero pausado
        else:
            logger.warning("El scheduler no está en ejecución para pausar trabajos.")

    def resume_all_jobs(self):
        """Reanuda todos los trabajos del scheduler."""
        if self._is_running:
            self.scheduler.resume()
            logger.info("Todos los trabajos del scheduler han sido reanudados.")
            self.scheduler_status_changed.emit(True) # Sigue corriendo y reanudado
        else:
            logger.warning("El scheduler no está en ejecución para reanudar trabajos.")

    def force_backup_now(self, config_id: int) -> bool:
        """Fuerza la ejecución inmediata de un respaldo para una configuración."""
        config = self.config_repo.get_by_id(config_id)
        if not config:
            logger.error(f"Configuración {config_id} no encontrada para forzar respaldo.")
            return False
        
        # Ejecutar el respaldo en un hilo separado
        self.backup_service.start_backup(config, is_manual=True)
        self.backup_executed.emit() # Emitir señal para refrescar la UI
        logger.info(f"Respaldo manual forzado para {config.name}.")
        return True

# Instancia global del servicio
scheduler_service = SchedulerService()
