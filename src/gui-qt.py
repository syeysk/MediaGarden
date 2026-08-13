import os
import sys

import django
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QModelIndex, QAbstractListModel

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from gardensunion.base.gui_main_window import MainWindow
from mediagarden.gui_entity_windows import GUIAnyFile
from mediagarden.scanner import STATUS_NEW, STATUS_DELETED

from django.conf import settings

ScanCardTypeRole = Qt.ItemDataRole.UserRole + 1


from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex


# TODO: Удалить
class ScanCardListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_list = [('test', STATUS_NEW), ('test2', STATUS_DELETED), ('test3', STATUS_NEW)]

    def rowCount(self, parent=QModelIndex):
        return len(self.data_list)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.data_list):
            return None
        
        # TODO: rename 'card_type' into 'status'
        value, card_type = self.data_list[index.row()]

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return value
        elif role == ScanCardTypeRole:
            print(card_type, role)
            return card_type
    
    # TODO: переименовать set_data в setData в лругом месте и проверить, добавляются ли строки автоматически
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        print(index, value)
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            card_type = self.data_list[index.row()][1]  # TODO: What the fuck?
            self.data_list[index.row()] = (value, card_type)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
            return True

        return False


class MainWindow(MainWindow):
    def __init__(self):
        self.gui_models = [GUIAnyFile]
        super().__init__()
        self.setWindowTitle('MediaGarden - Let\'s your knowledge to grow')
        self.setWindowIcon(QIcon(str(settings.BASE_DIR.parent / 'images/icon.png')))
        self.entity_types.select_current()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
