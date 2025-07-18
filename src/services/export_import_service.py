"""
Servicio de exportación e importación de configuraciones
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import zipfile
import shutil

from PyQt5.QtWidgets import QMessageBox

from ..models.backup_config import BackupConfig
from ..models.backup_history import BackupHistory
from ..models.app_settings import AppSettings
from ..models.backup_schedule import BackupSchedule
from ..repositories.backup_config_repository import backup_config_repository
from ..repositories.backup_history_repository import backup_history_repository
from ..repositories.app_settings_repository import app_settings_repository
from ..repositories.backup_schedule_repository import backup_schedule_repository
from ..services.encryption_service import encryption_service
from ..utils.helpers import show_message_box, parse_iso_datetime

logger = logging.getLogger(__name__)

class ExportImportService:
    def __init__(self):
        self.export_version = "1.0"
        self.config_repo = backup_config_repository
        self.history_repo = backup_history_repository
        self.settings_repo = app_settings_repository
        self.schedule_repo = backup_schedule_repository
        self.encryption_service = encryption_service
        logger.info("Servicio de exportación/importación inicializado.")
    
    def export_data(self, file_path: str) -> bool:
        """Exporta todas las configuraciones, programaciones y ajustes a un archivo JSON."""
        try:
            configs = self.config_repo.get_all()
            schedules = self.schedule_repo.get_all()
            settings = self.settings_repo.get_settings()

            # Convertir objetos a diccionarios para serialización
            export_data = {
                "configs": [config.to_dict() for config in configs],
                "schedules": [schedule.to_dict() for schedule in schedules],
                "settings": settings.to_dict() if settings else None,
                "export_timestamp": datetime.now().isoformat(),
                "export_version": self.export_version
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            
            logger.info(f"Datos exportados exitosamente a: {file_path}")
            show_message_box("Exportación Exitosa", f"Todos los datos han sido exportados a:\n{file_path}", QMessageBox.Information)
            return True
        except Exception as e:
            logger.error(f"Error al exportar datos: {e}")
            show_message_box("Error de Exportación", f"Ocurrió un error al exportar los datos:\n{e}", QMessageBox.Critical)
            return False

    def import_data(self, file_path: str) -> bool:
        """Importa configuraciones, programaciones y ajustes desde un archivo JSON."""
        reply = show_message_box("Confirmar Importación",
            "¿Está seguro que desea importar datos?\n"
            "Esto podría sobrescribir configuraciones y ajustes existentes, y añadir programaciones.",
            QMessageBox.Question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.No:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            imported_configs_count = 0
            imported_schedules_count = 0
            settings_updated = False

            # Importar configuraciones
            configs_data: List[Dict[str, Any]] = import_data.get("configs", [])
            for config_data in configs_data:
                # Eliminar ID para que se inserte como nuevo registro
                config_data.pop("id", None) 
                config_data.pop("created_at", None)
                config_data.pop("updated_at", None)

                # Asegurarse de que excluded_tables sea una lista (viene como JSON string del to_dict)
                if isinstance(config_data.get("excluded_tables"), str):
                    config_data["excluded_tables"] = json.loads(config_data["excluded_tables"])

                config = BackupConfig.from_dict(config_data)
                # Intentar añadir, si el nombre ya existe, actualizar
                existing_config = self.config_repo.get_by_name(config.name)
                if existing_config:
                    config.id = existing_config.id # Asignar ID para actualizar
                    # La contraseña en config.password_encrypted ya está desencriptada si viene del repo
                    # Si viene del archivo de importación, puede estar encriptada o no.
                    # El repositorio se encarga de re-encriptar si el valor "desencriptado" cambia.
                    if self.config_repo.update(config):
                        logger.info(f"Configuración '{config.name}' actualizada durante la importación.")
                    else:
                        logger.warning(f"No se pudo actualizar la configuración '{config.name}'.")
                else:
                    if self.config_repo.add(config):
                        imported_configs_count += 1
                        logger.info(f"Configuración '{config.name}' importada.")
                    else:
                        logger.warning(f"No se pudo importar la configuración '{config.name}'.")

            # Importar programaciones (se añaden nuevas, no se sobrescriben por ID de config)
            schedules_data: List[Dict[str, Any]] = import_data.get("schedules", [])
            for schedule_data in schedules_data:
                # Eliminar ID para que se inserte como nuevo registro
                schedule_data.pop("id", None)
                schedule_data.pop("created_at", None)
                schedule_data.pop("updated_at", None)
                schedule_data.pop("last_run_time", None) # No importar tiempos de ejecución pasados
                schedule_data.pop("next_run_time", None) # Se recalculará al cargar

                # Asegurarse de que days_of_week sea una lista (viene como JSON string del to_dict)
                if isinstance(schedule_data.get("days_of_week"), str):
                    schedule_data["days_of_week"] = json.loads(schedule_data["days_of_week"])

                schedule = BackupSchedule.from_dict(schedule_data)
                # Verificar si la config_id referenciada existe
                if self.config_repo.get_by_id(schedule.config_id):
                    # Verificar si ya existe una programación para esta configuración
                    existing_schedule_for_config = self.schedule_repo.get_by_config_id(schedule.config_id)
                    if existing_schedule_for_config:
                        # Si ya existe, actualizarla
                        schedule.id = existing_schedule_for_config.id
                        if self.schedule_repo.update(schedule):
                            imported_schedules_count += 1
                            logger.info(f"Programación para config_id {schedule.config_id} actualizada durante la importación.")
                        else:
                            logger.warning(f"No se pudo actualizar la programación para config_id {schedule.config_id}.")
                    else:
                        # Si no existe, añadirla
                        if self.schedule_repo.add(schedule):
                            imported_schedules_count += 1
                            logger.info(f"Programación para config_id {schedule.config_id} importada.")
                        else:
                            logger.warning(f"No se pudo importar la programación para config_id {schedule.config_id}.")
                else:
                    logger.warning(f"Programación para config_id {schedule.config_id} omitida: la configuración de base de datos no existe.")

            # Importar settings (reemplazar existentes)
            settings_data: Optional[Dict[str, Any]] = import_data.get("settings")
            if settings_data:
                # Eliminar ID para que se actualice la única fila existente
                settings_data.pop("id", None)
                settings_data.pop("created_at", None)
                settings_data.pop("updated_at", None)

                settings = AppSettings.from_dict(settings_data)
                # La contraseña de email en settings.email_password_encrypted puede estar encriptada o no.
                # El repositorio se encarga de re-encriptar si el valor "desencriptado" cambia.
                if self.settings_repo.save_settings(settings):
                    settings_updated = True
                    logger.info("Ajustes de aplicación importados/actualizados.")
                else:
                    logger.warning("No se pudieron importar/actualizar los ajustes de la aplicación.")

            msg = f"Importación completada:\n" \
                  f"- {imported_configs_count} configuraciones importadas/actualizadas.\n" \
                  f"- {imported_schedules_count} programaciones importadas/actualizadas.\n" \
                  f"- Ajustes de aplicación: {'Actualizados' if settings_updated else 'No actualizados/No presentes en el archivo'}."
            logger.info(msg)
            show_message_box("Importación Exitosa", msg, QMessageBox.Information)
            return True
        except json.JSONDecodeError:
            logger.error(f"Error: El archivo '{file_path}' no es un JSON válido.")
            show_message_box("Error de Importación", f"El archivo '{file_path}' no es un JSON válido.", QMessageBox.Critical)
            return False
        except Exception as e:
            logger.error(f"Error al importar datos: {e}")
            show_message_box("Error de Importación", f"Ocurrió un error al importar los datos:\n{e}", QMessageBox.Critical)
            return False
