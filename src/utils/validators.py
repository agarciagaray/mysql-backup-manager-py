import os
import re
import json
from typing import List, Optional, Any

def is_valid_port(port: str) -> bool:
    """Valida si un puerto es un número entero entre 1 y 65535."""
    try:
        p = int(port)
        return 1 <= p <= 65535
    except ValueError:
        return False

def is_valid_path(path: str) -> bool:
    """Valida si una ruta es un directorio existente."""
    return os.path.isdir(path)

def is_valid_file_path(path: str) -> bool:
    """Valida si una ruta es un archivo existente."""
    return os.path.isfile(path)

def is_valid_retention_days(days: str) -> bool:
    """Valida si los días de retención son un número entero no negativo."""
    try:
        d = int(days)
        return d >= 0
    except ValueError:
        return False

def is_valid_time_format(time_str: str) -> bool:
    """Valida si una cadena de tiempo está en formato HH:MM."""
    return re.fullmatch(r"^(?:2[0-3]|[01]?[0-9]):(?:[0-5]?[0-9])$", time_str) is not None

def is_valid_days_of_week(days_list: List[int]) -> bool:
    """Valida si una lista de enteros representa días de la semana válidos (0-6)."""
    if not isinstance(days_list, list):
        return False
    return all(isinstance(d, int) and 0 <= d <= 6 for d in days_list)

def is_valid_day_of_month(day: str) -> bool:
    """Valida si un día del mes es un número entero entre 1 y 31."""
    try:
        d = int(day)
        return 1 <= d <= 31
    except ValueError:
        return False

def is_valid_email(email: str) -> bool:
    """Valida si una cadena es un formato de correo electrónico válido."""
    # Expresión regular simple para validación de email
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_host(host: str) -> bool:
    """Valida si una cadena es una dirección IP válida (IPv4) o un nombre de host."""
    # Simple regex para IPv4
    ipv4_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
    if ipv4_pattern.match(host):
        parts = list(map(int, host.split('.')))
        return all(0 <= part <= 255 for part in parts)
    
    # Simple regex para hostname (no exhaustivo, pero cubre casos comunes)
    hostname_pattern = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$")
    if hostname_pattern.match(host):
        return True
    
    # Permitir 'localhost'
    if host.lower() == 'localhost':
        return True
        
    return False
