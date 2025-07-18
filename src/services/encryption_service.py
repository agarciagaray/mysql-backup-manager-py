import os
from cryptography.fernet import Fernet
import logging

from ..utils.helpers import get_app_data_path
from ..utils.constants import ENCRYPTION_KEY_FILE

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self):
        self.key_file = get_app_data_path(ENCRYPTION_KEY_FILE)
        self._key = self._load_or_generate_key()
        self.fernet = Fernet(self._key)
        logger.info("Servicio de encriptación inicializado.")

    def _load_or_generate_key(self) -> bytes:
        """Carga la clave de encriptación desde un archivo o genera una nueva."""
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                key = f.read()
            logger.debug(f"Clave de encriptación cargada desde: {self.key_file}")
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            logger.info(f"Nueva clave de encriptación generada y guardada en: {self.key_file}")
        return key

    def encrypt(self, data: str) -> str:
        """Encripta una cadena de texto."""
        if not data:
            return ""
        try:
            encrypted_data = self.fernet.encrypt(data.encode()).decode()
            logger.debug("Datos encriptados.")
            return encrypted_data
        except Exception as e:
            logger.error(f"Error al encriptar datos: {e}")
            return ""

    def decrypt(self, encrypted_data: str) -> str:
        """Desencripta una cadena de texto."""
        if not encrypted_data:
            return ""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode()).decode()
            logger.debug("Datos desencriptados.")
            return decrypted_data
        except Exception as e:
            logger.error(f"Error al desencriptar datos: {e}")
            return ""

# Instancia global del servicio de encriptación
encryption_service = EncryptionService()
