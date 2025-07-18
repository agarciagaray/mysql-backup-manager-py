import subprocess
import os
import shutil
import logging
import threading
from datetime import datetime
from typing import Optional, Tuple

from ..models.backup_config import BackupConfig
from ..models.backup_history import BackupHistory
from ..repositories.backup_history_repository import backup_history_repository
from ..services.notification_service import notification_service
from ..utils.constants import BACKUP_STATUS_RUNNING, BACKUP_STATUS_SUCCESS, BACKUP_STATUS_FAILED, BACKUP_STATUS_CANCELLED
from ..utils.helpers import format_bytes, get_current_timestamp

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.history_repo = backup_history_repository
        self.notification_service = notification_service
        self.running_backups_threads = {} # {config_id: threading.Thread}
        logger.info("Servicio de respaldo inicializado.")

    def _run_mysqldump(self, config: BackupConfig, output_file: str) -> Tuple[bool, str]:
        """Ejecuta el comando mysqldump."""
        try:
            # Construir el comando mysqldump
            command = [
                config.mysqldump_path,
                f"--host={config.host}",
                f"--port={config.port}",
                f"--user={config.username}",
                config.database_name
            ]
            if config.password_encrypted: # La contraseña ya viene desencriptada del repo
                command.append(f"--password={config.password_encrypted}")
            
            # Excluir tablas si se especifican
            for table in config.excluded_tables:
                command.append(f"--ignore-table={config.database_name}.{table}")

            logger.info(f"Ejecutando mysqldump para {config.name}...")
            # Ocultar contraseña en log
            log_command = [cmd if not cmd.startswith("--password=") else "--password=********" for cmd in command]
            logger.debug(f"Comando: {' '.join(log_command)}") 

            # Usar subprocess.Popen para capturar stdout y stderr por separado
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = process.communicate() # Esperar a que termine el proceso

            if process.returncode != 0:
                error_message = stderr.strip()
                logger.error(f"mysqldump falló para {config.name}: {error_message}")
                return False, error_message
            
            # Escribir la salida de mysqldump al archivo SQL
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(stdout)

            logger.info(f"mysqldump completado exitosamente para {config.name}.")
            return True, "mysqldump completado."

        except FileNotFoundError:
            error_message = f"mysqldump no encontrado en la ruta: {config.mysqldump_path}. Por favor, verifica la configuración."
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Error inesperado al ejecutar mysqldump para {config.name}: {e}"
            logger.error(error_message)
            return False, error_message

    def _compress_file(self, input_file: str, compression_method: str) -> Tuple[bool, str, Optional[str]]:
        """Comprime el archivo de respaldo según el método especificado."""
        if compression_method == "none":
            return True, "Sin compresión.", input_file
        
        output_file = f"{input_file}.{compression_method}"
        try:
            logger.info(f"Comprimiendo archivo con {compression_method}...")
            if compression_method == "zip":
                # Crear un archivo zip que contenga el archivo SQL
                # shutil.make_archive crea un archivo con extensión .zip, no necesitamos añadirla
                base_name = os.path.splitext(input_file)[0] # Nombre sin extensión .sql
                archive_name = shutil.make_archive(base_name, 'zip', root_dir=os.path.dirname(input_file), base_dir=os.path.basename(input_file))
                os.remove(input_file) # Eliminar el archivo .sql original
                return True, "Archivo comprimido con ZIP.", archive_name
            elif compression_method == "gzip":
                import gzip
                with open(input_file, 'rb') as f_in:
                    with gzip.open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(input_file) # Eliminar el archivo .sql original
                return True, "Archivo comprimido con GZIP.", output_file
            else:
                return False, f"Método de compresión '{compression_method}' no soportado.", None
        except Exception as e:
            logger.error(f"Error al comprimir el archivo: {e}")
            return False, f"Error al comprimir: {e}", None

    def _clean_old_backups(self, config: BackupConfig):
        """Elimina respaldos antiguos según la política de retención."""
        logger.info(f"Limpiando respaldos antiguos para {config.name}...")
        backup_dir = config.backup_path
        
        if not os.path.exists(backup_dir):
            logger.warning(f"Directorio de respaldo no encontrado para limpieza: {backup_dir}")
            return

        now = datetime.now()
        
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path):
                try:
                    # Intentar parsear la fecha del nombre del archivo (YYYYMMDD_HHMMSS)
                    # Asumimos el formato de nombre de archivo: {db_name}_{timestamp}.sql(.zip/.gz)
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        date_part = parts[-2] # YYYYMMDD
                        time_part = parts[-1].split('.')[0] # HHMMSS
                        file_datetime_str = f"{date_part}_{time_part}"
                        file_datetime = datetime.strptime(file_datetime_str, "%Y%m%d_%H%M%S")
                    else:
                        # Si el nombre no sigue el formato esperado, usar la fecha de modificación
                        file_datetime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    age_days = (now - file_datetime).days

                    # Política de retención principal (más reciente)
                    if age_days >= config.retention_days_main:
                        # Política de retención segregada (más antigua)
                        if age_days >= config.retention_days_segregated:
                            logger.info(f"Eliminando respaldo antiguo (segregado): {filename} ({age_days} días)")
                            os.remove(file_path)
                        else:
                            # Mantener respaldos entre retention_days_main y retention_days_segregated
                            # Aquí podrías moverlos a un subdirectorio "segregado" si quisieras
                            pass
                except Exception as e:
                    logger.warning(f"No se pudo procesar el archivo {filename} para limpieza: {e}")
        logger.info(f"Limpieza de respaldos para {config.name} completada.")

    def _perform_backup_task(self, config: BackupConfig, is_manual: bool = False):
        """Tarea principal que ejecuta el respaldo en un hilo."""
        logger.info(f"Iniciando respaldo para la configuración: {config.name} (Manual: {is_manual})")
        
        # Crear un registro de historial inicial
        history = BackupHistory(
            config_id=config.id,
            config_name=config.name,
            start_time=datetime.now(),
            status=BACKUP_STATUS_RUNNING,
            is_manual=is_manual
        )
        history = self.history_repo.add(history)
        if not history:
            logger.error(f"No se pudo crear el registro de historial para {config.name}.")
            self.notification_service.send_email_notification(
                f"Error de Respaldo: {config.name}",
                f"No se pudo crear el registro de historial para el respaldo de {config.name}.",
                'error'
            )
            return

        backup_status = BACKUP_STATUS_FAILED
        backup_message = "Respaldo fallido."
        final_file_path = None
        file_size = 0
        start_time = datetime.now()
        log_output = ""

        try:
            # 1. Crear directorio de respaldo si no existe
            os.makedirs(config.backup_path, exist_ok=True)

            # 2. Generar nombre de archivo temporal y final
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_sql_file = os.path.join(config.backup_path, f"{config.database_name}_{timestamp}.sql")
            
            # 3. Ejecutar mysqldump
            success, message = self._run_mysqldump(config, temp_sql_file)
            log_output += f"mysqldump: {message}\n"

            if not success:
                backup_message = f"mysqldump falló: {message}"
                self.notification_service.send_email_notification(
                    f"Respaldo Fallido: {config.name}",
                    f"El respaldo de {config.name} falló durante mysqldump: {message}",
                    'error'
                )
                return # Salir si mysqldump falla

            # 4. Comprimir el archivo si es necesario
            if config.compression_method != "none":
                compress_success, compress_message, compressed_file = self._compress_file(temp_sql_file, config.compression_method)
                log_output += f"Compresión: {compress_message}\n"
                if not compress_success:
                    backup_message = f"Compresión fallida: {compress_message}"
                    self.notification_service.send_email_notification(
                        f"Respaldo Fallido: {config.name}",
                        f"El respaldo de {config.name} falló durante la compresión: {compress_message}",
                        'error'
                    )
                    return
                final_file_path = compressed_file
            else:
                final_file_path = temp_sql_file
            
            # 5. Obtener tamaño del archivo final
            if final_file_path and os.path.exists(final_file_path):
                file_size = os.path.getsize(final_file_path)
                log_output += f"Tamaño del archivo: {format_bytes(file_size)}\n"
            else:
                log_output += "Advertencia: No se pudo determinar el tamaño del archivo final.\n"

            backup_status = BACKUP_STATUS_SUCCESS
            backup_message = "Respaldo completado exitosamente."
            logger.info(f"Respaldo exitoso para {config.name}. Archivo: {final_file_path}")
            self.notification_service.send_email_notification(
                f"Respaldo Exitoso: {config.name}",
                f"El respaldo de {config.name} se completó exitosamente. Archivo: {final_file_path} (Tamaño: {format_bytes(file_size)})",
                'info'
            )

        except Exception as e:
            backup_status = BACKUP_STATUS_FAILED
            backup_message = f"Error inesperado durante el respaldo: {e}"
            logger.critical(f"Error crítico en el respaldo para {config.name}: {e}", exc_info=True)
            self.notification_service.send_email_notification(
                f"Respaldo Crítico Fallido: {config.name}",
                f"Un error crítico ocurrió durante el respaldo de {config.name}: {e}",
                'error'
            )
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Actualizar el registro de historial
            history.end_time = end_time
            history.status = backup_status
            history.message = backup_message
            history.file_path = final_file_path
            history.file_size = file_size
            history.duration_seconds = duration
            history.log_output = log_output
            self.history_repo.update(history)
            
            # Limpiar respaldos antiguos
            if backup_status == BACKUP_STATUS_SUCCESS:
                self._clean_old_backups(config)
            
            # Eliminar el hilo de la lista de respaldos en ejecución
            if config.id in self.running_backups_threads:
                del self.running_backups_threads[config.id]
            logger.info(f"Tarea de respaldo para {config.name} finalizada.")

    def start_backup(self, config: BackupConfig, is_manual: bool = False) -> bool:
        """Inicia un respaldo en un hilo separado."""
        if config.id is None:
            logger.error("No se puede iniciar el respaldo: ID de configuración no válido.")
            self.notification_service.show_error("Error de Respaldo", "ID de configuración no válido.")
            return False

        if config.id in self.running_backups_threads and self.running_backups_threads[config.id].is_alive():
            logger.warning(f"El respaldo para '{config.name}' ya está en ejecución.")
            self.notification_service.show_warning("Respaldo en Curso", f"El respaldo para '{config.name}' ya está en ejecución.")
            return False

        thread = threading.Thread(
            target=self._perform_backup_task,
            args=(config, is_manual),
            daemon=True # Permite que el programa se cierre aunque el hilo esté corriendo
        )
        self.running_backups_threads[config.id] = thread
        thread.start()
        logger.info(f"Hilo de respaldo iniciado para '{config.name}'.")
        return True

    def is_backup_running(self, config_id: int) -> bool:
        """Verifica si un respaldo para una configuración específica está en ejecución."""
        thread = self.running_backups_threads.get(config_id)
        return thread is not None and thread.is_alive()

# Instancia global del servicio de respaldo
backup_service = BackupService()
