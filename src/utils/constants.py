import os

# Configuración de la aplicación
APP_NAME = "MySQL Backup Manager"
APP_VERSION = "1.0.0"
APP_AUTHOR = "v0"

# Directorio base para datos de la aplicación (depende del SO)
# En Windows: C:\Users\<User>\AppData\Local\MySQLBackupManager
# En Linux: ~/.local/share/MySQLBackupManager
# En macOS: ~/Library/Application Support/MySQLBackupManager
APP_DATA_DIR_NAME = "MySQLBackupManager"

# Archivos de la base de datos
DB_FILE = "app.db"
# DB_PATH se construirá dinámicamente usando get_app_data_path

# Archivo de clave de encriptación
ENCRYPTION_KEY_FILE = "encryption.key"
# ENCRYPTION_KEY_PATH se construirá dinámicamente usando get_app_data_path

# Esquema de la base de datos SQLite
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_width INTEGER DEFAULT 1024,
    window_height INTEGER DEFAULT 768,
    window_maximized BOOLEAN DEFAULT 0,
    auto_start_scheduler BOOLEAN DEFAULT 1,
    notification_level TEXT DEFAULT 'info', -- 'info', 'warning', 'error'
    log_retention_days INTEGER DEFAULT 30,
    default_backup_path TEXT,
    default_mysqldump_path TEXT,
    email_notifications_enabled BOOLEAN DEFAULT 0,
    email_recipient TEXT,
    email_smtp_server TEXT,
    email_smtp_port INTEGER,
    email_username TEXT,
    email_password_encrypted TEXT,
    email_sender_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS database_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    host TEXT NOT NULL,
    port INTEGER DEFAULT 3306,
    username TEXT NOT NULL,
    password_encrypted TEXT,
    database_name TEXT NOT NULL,
    mysqldump_path TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    excluded_tables TEXT, -- JSON string of list of tables
    compression_method TEXT DEFAULT 'zip', -- 'zip', 'gzip', 'none'
    retention_days_main INTEGER DEFAULT 7,
    retention_days_segregated INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    config_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    status TEXT NOT NULL, -- 'running', 'success', 'failed', 'cancelled'
    file_path TEXT,
    file_size INTEGER, -- in bytes
    duration_seconds REAL,
    log_output TEXT,
    is_manual BOOLEAN DEFAULT 0,
    FOREIGN KEY (config_id) REFERENCES database_configs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS backup_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    schedule_type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'
    time TEXT NOT NULL, -- HH:MM format
    days_of_week TEXT, -- JSON string for weekly schedules (e.g., "[0, 1, 2]" for Sun, Mon, Tue)
    day_of_month INTEGER, -- For monthly schedules (1-31)
    is_active BOOLEAN DEFAULT 1,
    last_run_time TEXT,
    next_run_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES database_configs(id) ON DELETE CASCADE
);
"""

# Estados de respaldo
BACKUP_STATUS_RUNNING = "running"
BACKUP_STATUS_SUCCESS = "success"
BACKUP_STATUS_FAILED = "failed"
BACKUP_STATUS_CANCELLED = "cancelled"

# Métodos de compresión
COMPRESSION_METHODS = ["zip", "gzip", "none"]

# Tipos de programación
SCHEDULE_TYPE_DAILY = "daily"
SCHEDULE_TYPE_WEEKLY = "weekly"
SCHEDULE_TYPE_MONTHLY = "monthly"
SCHEDULE_TYPES = [SCHEDULE_TYPE_DAILY, SCHEDULE_TYPE_WEEKLY, SCHEDULE_TYPE_MONTHLY]

# Días de la semana para programación (0=Domingo, 6=Sábado)
DAYS_OF_WEEK = {
    0: "Domingo",
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado"
}

# Niveles de notificación
NOTIFICATION_LEVELS = ["info", "warning", "error"]

# Configuración de logging
LOG_FILE_NAME = "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
