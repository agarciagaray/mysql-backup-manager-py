import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QColor

from ...repositories.backup_history_repository import backup_history_repository
from ...utils.helpers import format_bytes, format_duration

logger = logging.getLogger(__name__)

class BackupHistoryTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_repo = backup_history_repository
        self._init_ui()
        self.load_history()
        logger.info("Tabla de historial de respaldos inicializada.")

    def _init_ui(self):
        """Inicializa la tabla de historial de respaldos."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Configuración", "Inicio", "Fin", "Duración",
            "Estado", "Archivo", "Tamaño", "Manual"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # Hacer la tabla de solo lectura
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.main_layout.addWidget(self.table)

    def load_history(self):
        """Carga los datos del historial de respaldos en la tabla."""
        logger.debug("Cargando historial de respaldos...")
        history_items = self.history_repo.get_all()
        self.table.setRowCount(len(history_items))

        for row_idx, item in enumerate(history_items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.config_name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.start_time.strftime("%Y-%m-%d %H:%M:%S") if item.start_time else "N/A"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.end_time.strftime("%Y-%m-%d %H:%M:%S") if item.end_time else "N/A"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(format_duration(item.duration_seconds)))
            
            status_item = QTableWidgetItem(item.status)
            if item.status == "success":
                status_item.setForeground(QColor("green"))
            elif item.status == "failed":
                status_item.setForeground(QColor("red"))
            elif item.status == "running":
                status_item.setForeground(QColor("blue"))
            elif item.status == "cancelled":
                status_item.setForeground(QColor("orange"))
            self.table.setItem(row_idx, 5, status_item)

            self.table.setItem(row_idx, 6, QTableWidgetItem(item.file_path if item.file_path else "N/A"))
            self.table.setItem(row_idx, 7, QTableWidgetItem(format_bytes(item.file_size) if item.file_size is not None else "N/A"))
            self.table.setItem(row_idx, 8, QTableWidgetItem("Sí" if item.is_manual else "No"))
        
        self.table.resizeColumnsToContents()
        logger.debug(f"Historial de respaldos cargado: {len(history_items)} elementos.")

    def _show_context_menu(self, pos):
        """Muestra el menú contextual al hacer clic derecho en la tabla."""
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        selected_row = index.row()
        history_id = int(self.table.item(selected_row, 0).text())

        menu = QMenu(self)
        view_log_action = menu.addAction("Ver Log")
        delete_action = menu.addAction("Eliminar Registro")

        action = menu.exec_(self.table.viewport().mapToGlobal(pos))

        if action == view_log_action:
            self._view_log(history_id)
        elif action == delete_action:
            self._delete_history_item(history_id)

    def _view_log(self, history_id: int):
        """Muestra el log de un respaldo específico."""
        item = self.history_repo.get_by_id(history_id)
        if item and item.log_output:
            QMessageBox.information(self, f"Log de Respaldo (ID: {history_id})", item.log_output)
            logger.info(f"Log de respaldo ID {history_id} visualizado.")
        else:
            QMessageBox.information(self, "Log no disponible", "No hay log disponible para este respaldo.")
            logger.warning(f"Intento de ver log para ID {history_id} sin log disponible.")

    def _delete_history_item(self, history_id: int):
        """Elimina un registro del historial."""
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar el registro de historial ID {history_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.history_repo.delete(history_id):
                QMessageBox.information(self, "Eliminación Exitosa", "Registro eliminado correctamente.")
                self.load_history() # Recargar la tabla
                logger.info(f"Registro de historial ID {history_id} eliminado.")
            else:
                QMessageBox.warning(self, "Error de Eliminación", "No se pudo eliminar el registro.")
                logger.error(f"Error al eliminar registro de historial ID {history_id}.")
