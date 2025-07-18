import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from PyQt5.QtWidgets import QMessageBox

from ..repositories.app_settings_repository import app_settings_repository
from ..utils.constants import NOTIFICATION_LEVELS
from ..utils.helpers import show_message_box

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.settings_repo = app_settings_repository
        logger.info("Servicio de notificaciones inicializado.")

    def _should_notify(self, message_level: str) -> bool:
        """Determina si se debe enviar una notificación basándose en el nivel configurado."""
        settings = self.settings_repo.get_settings()
        configured_level = settings.notification_level
        
        if configured_level not in NOTIFICATION_LEVELS:
            logger.warning(f"Nivel de notificación configurado inválido: {configured_level}. Usando 'info'.")
            configured_level = 'info'

        configured_index = NOTIFICATION_LEVELS.index(configured_level)
        message_index = NOTIFICATION_LEVELS.index(message_level)
        
        return message_index >= configured_index

    def show_info(self, title: str, message: str):
        """Muestra un mensaje informativo en la UI."""
        show_message_box(title, message, QMessageBox.Information)
        logger.info(f"INFO - {title}: {message}")

    def show_warning(self, title: str, message: str):
        """Muestra un mensaje de advertencia en la UI."""
        show_message_box(title, message, QMessageBox.Warning)
        logger.warning(f"WARNING - {title}: {message}")

    def show_error(self, title: str, message: str):
        """Muestra un mensaje de error en la UI."""
        show_message_box(title, message, QMessageBox.Critical)
        logger.error(f"ERROR - {title}: {message}")

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Muestra un diálogo de sí/no y retorna la respuesta booleana."""
        reply = show_message_box(title, message, QMessageBox.Question, 
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def send_email_notification(self, subject: str, body: str, message_level: str = 'info'):
        """Envía una notificación por correo electrónico si las notificaciones están habilitadas y el nivel lo permite."""
        settings = self.settings_repo.get_settings()

        if not settings.email_notifications_enabled:
            logger.debug("Notificaciones por correo electrónico deshabilitadas.")
            return
        
        if not self._should_notify(message_level):
            logger.info(f"Notificación de nivel '{message_level}' omitida debido a la configuración de nivel '{settings.notification_level}'.")
            return

        if not all([settings.email_recipient, settings.email_smtp_server, settings.email_smtp_port, settings.email_username, settings.email_password_encrypted]):
            logger.error("Faltan configuraciones de correo electrónico para enviar la notificación.")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{settings.email_sender_name} <{settings.email_username}>" if settings.email_sender_name else settings.email_username
            msg['To'] = settings.email_recipient
            msg['Subject'] = f"[{message_level.upper()}] {subject}"
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port) as server:
                server.starttls() # Habilitar seguridad TLS
                server.login(settings.email_username, settings.email_password_encrypted) # password_encrypted ya viene desencriptada del repo
                server.send_message(msg)
            logger.info(f"Notificación por correo electrónico enviada a {settings.email_recipient} con asunto: {subject}")
        except Exception as e:
            logger.error(f"Error al enviar notificación por correo electrónico: {e}")

# Instancia global del servicio de notificaciones
notification_service = NotificationService()
