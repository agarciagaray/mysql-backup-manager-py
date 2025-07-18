import logging
import mysql.connector
from typing import List, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from ...models.backup_config import BackupConfig
from ...services.encryption_service import encryption_service
from ...utils.helpers import get_icon

logger = logging.getLogger(__name__)

class TableLoadThread(QThread):
    """Hilo para cargar las tablas de una base de datos."""
    tables_loaded = pyqtSignal(list)
    load_error = pyqtSignal(str)

    def __init__(self, config: BackupConfig, parent=None):
        super().__init__(parent)
        self.config = config
        logger.debug(f"Hilo de carga de tablas creado para {config.name}.")

    def run(self):
        try:
            cnx = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password_encrypted,
                database=self.config.database_name,
                connection_timeout=5
            )
            cursor = cnx.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor]
            cursor.close()
            cnx.close()
            self.tables_loaded.emit(tables)
            logger.info(f"Tablas cargadas exitosamente para {self.config.name}.")
        except mysql.connector.Error as err:
            self.load_error.emit(f"Error al cargar tablas: {err}")
            logger.error(f"Error al cargar tablas para {self.config.name}: {err}")
        except Exception as e:
            self.load_error.emit(f"Error inesperado al cargar tablas: {e}")
            logger.error(f"Error inesperado al cargar tablas para {self.config.name}: {e}")

class TableSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.encryption_service = encryption_service
        self.current_config: Optional[BackupConfig] = None
        self.available_tables = []
        self.excluded_tables = []
        self._init_ui()
        logger.info("Selector de tablas inicializado.")

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        # Botón para cargar tablas
        self.load_tables_button = QPushButton(get_icon("refresh"), "Cargar Tablas")
        self.load_tables_button.clicked.connect(self._start_load_tables)
        self.main_layout.addWidget(self.load_tables_button)

        self.status_label = QLabel("Estado: Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_label)

        # Búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar tabla...")
        self.search_input.textChanged.connect(self._filter_available_tables)
        search_layout.addWidget(self.search_input)
        self.main_layout.addLayout(search_layout)

        # Listas y botones de transferencia
        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(10)

        # Lista de tablas disponibles
        self.available_tables_list = QListWidget()
        self.available_tables_list.setSelectionMode(QListWidget.MultiSelection)
        lists_layout.addWidget(self.available_tables_list)

        # Botones de transferencia
        button_column_layout = QVBoxLayout()
        button_column_layout.addStretch(1)
        self.add_button = QPushButton(">>")
        self.add_button.clicked.connect(self._add_selected_tables)
        button_column_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("<<")
        self.remove_button.clicked.connect(self._remove_selected_tables)
        button_column_layout.addWidget(self.remove_button)
        button_column_layout.addStretch(1)
        lists_layout.addLayout(button_column_layout)

        # Lista de tablas excluidas
        self.excluded_tables_list = QListWidget()
        self.excluded_tables_list.setSelectionMode(QListWidget.MultiSelection)
        lists_layout.addWidget(self.excluded_tables_list)

        self.main_layout.addLayout(lists_layout)

        self.setStyleSheet("""
            TableSelector QLabel {
                font-weight: bold;
                color: #555555;
            }
            TableSelector QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-height: 100px;
            }
            TableSelector QListWidget::item:selected {
                background-color: #e0e0e0;
                color: #333333;
            }
            TableSelector QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            TableSelector QPushButton:hover {
                background-color: #0056b3;
            }
            TableSelector QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)

    def set_config(self, config: BackupConfig):
        """Establece la configuración de la base de datos para cargar tablas."""
        self.current_config = config
        self.status_label.setText("Estado: Listo")
        self.status_label.setStyleSheet("")
        self.available_tables_list.clear()
        self.excluded_tables_list.clear()
        logger.debug(f"Configuración de tablas establecida para {config.name}.")

    def _start_load_tables(self):
        """Inicia la carga de tablas en un hilo separado."""
        if not self.current_config:
            self.status_label.setText("Estado: No hay configuración para cargar tablas.")
            self.status_label.setStyleSheet("color: orange;")
            logger.warning("Intento de cargar tablas sin configuración establecida.")
            return

        self.status_label.setText("Estado: Cargando tablas...")
        self.status_label.setStyleSheet("color: blue;")
        self.load_tables_button.setEnabled(False)
        self.available_tables_list.clear()
        self.excluded_tables_list.clear()

        self.load_thread = TableLoadThread(self.current_config)
        self.load_thread.tables_loaded.connect(self._on_tables_loaded)
        self.load_thread.load_error.connect(self._on_load_error)
        self.load_thread.start()
        logger.info(f"Iniciando carga de tablas para {self.current_config.name}.")

    def _on_tables_loaded(self, tables: List[str]):
        """Maneja las tablas cargadas."""
        self.load_tables_button.setEnabled(True)
        self.status_label.setText("Estado: Tablas cargadas.")
        self.status_label.setStyleSheet("color: green;")
        self.available_tables = sorted(tables)
        self._populate_lists()
        logger.info(f"Tablas cargadas: {len(tables)}.")

    def _on_load_error(self, error_message: str):
        """Maneja errores al cargar tablas."""
        self.load_tables_button.setEnabled(True)
        self.status_label.setText(f"Estado: {error_message}")
        self.status_label.setStyleSheet("color: red;")
        logger.error(f"Error al cargar tablas: {error_message}")

    def get_selected_tables(self) -> List[str]:
        """Retorna las tablas seleccionadas en la lista."""
        return [item.text() for item in self.available_tables_list.selectedItems()]

    def set_selected_tables(self, excluded_tables: List[str]):
        """Selecciona las tablas en la lista que están en la lista de excluidas."""
        for i in range(self.available_tables_list.count()):
            item = self.available_tables_list.item(i)
            if item.text() in excluded_tables:
                item.setSelected(True)
            else:
                item.setSelected(False)
        logger.debug(f"Tablas excluidas pre-seleccionadas: {excluded_tables}")

    def _populate_lists(self):
        """Rellena las listas de disponibles y excluidas."""
        self.available_tables_list.clear()
        self.excluded_tables_list.clear()

        current_excluded = set(self.excluded_tables)
        
        for table in self.available_tables:
            if table in current_excluded:
                self.excluded_tables_list.addItem(table)
            else:
                self.available_tables_list.addItem(table)
        
        self._filter_available_tables(self.search_input.text()) # Aplicar filtro si hay texto
        logger.debug("Listas de tablas disponibles y excluidas repobladas.")

    def _filter_available_tables(self, text: str):
        """Filtra la lista de tablas disponibles según el texto de búsqueda."""
        for i in range(self.available_tables_list.count()):
            item = self.available_tables_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _add_selected_tables(self):
        """Mueve las tablas seleccionadas de 'disponibles' a 'excluidas'."""
        selected_items = self.available_tables_list.selectedItems()
        for item in selected_items:
            self.available_tables_list.takeItem(self.available_tables_list.row(item))
            self.excluded_tables_list.addItem(item.text())
        self.excluded_tables_list.sortItems(Qt.AscendingOrder)
        logger.debug(f"{len(selected_items)} tablas añadidas a la lista de excluidas.")

    def _remove_selected_tables(self):
        """Mueve las tablas seleccionadas de 'excluidas' a 'disponibles'."""
        selected_items = self.excluded_tables_list.selectedItems()
        for item in selected_items:
            self.excluded_tables_list.takeItem(self.excluded_tables_list.row(item))
            self.available_tables_list.addItem(item.text())
        self.available_tables_list.sortItems(Qt.AscendingOrder)
        self._filter_available_tables(self.search_input.text()) # Re-aplicar filtro
        logger.debug(f"{len(selected_items)} tablas removidas de la lista de excluidas.")
