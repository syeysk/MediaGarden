import os
import sys
from struct import unpack

import django
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QModelIndex, QAbstractListModel

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from mediagarden.gui_entities_list import FilesList
from mediagarden.gui_entity_windows import FileWindow
from common.gui_entity import GUIEntity
from common.gui_main_window import MainWindow
from mediagarden.gui_actions import ActionsAnyFileWidget
from mediagarden.models import AnyFile
from scanner import (
    STATUS_NEW, STATUS_MOVED, STATUS_RENAMED, STATUS_MOVED_AND_RENAMED,
    STATUS_UNTOUCHED, STATUS_DELETED, STATUS_DUPLICATE,
)

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


class ScanTaskDeletedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Удалён с диска')
        layout.addWidget(lbl_title)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_delete = QPushButton('Удалить из базы')
        layout.addWidget(btn_delete)


class ScanTaskDuplicateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Дубликат')
        layout.addWidget(lbl_title)

        self.lbl_inserted_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_delete_from_disk = QPushButton('Удалить')
        lbl_on_disk = QLabel('Есть на диске')
        layout_inserted = QHBoxLayout()
        layout_inserted.addWidget(btn_delete_from_disk)
        layout_inserted.addWidget(lbl_on_disk)
        layout.addLayout(layout_inserted)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_delete = QPushButton('Удалить')
        lbl_on_both = QLabel('Есть на диске и в базе')
        layout_existed = QHBoxLayout()
        layout_existed.addWidget(btn_delete)
        layout_existed.addWidget(lbl_on_both)
        layout.addLayout(layout_existed)


class ScanTaskMovedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel('Перемещён')
        layout.addWidget(lbl_title)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        self.lbl_inserted_path = QLabel()
        layout.addWidget(self.lbl_existed_path)

        btn_cancel = QPushButton('Отменить')
        btn_cancel.setDisabled(True)  # TODO: реализовать функционал и удалить эту строку
        btn_accept = QPushButton('Подтвердить')
        btn_accept.setDisabled(True)  # TODO: реализовать функционал и удалить эту строку
        layout_btns = QHBoxLayout()
        layout_btns.addWidget(btn_cancel)
        layout_btns.addWidget(btn_accept)
        layout.addLayout(layout_btns)


class ScanTaskNewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Новый')
        layout.addWidget(lbl_title)

        self.lbl_inserted_path = QLabel()
        layout.addWidget(self.lbl_inserted_path)

        btn_delete = QPushButton('Удалить')
        layout.addWidget(btn_delete)


class ScanTaskUntouchedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel('Неизменён')
        layout.addWidget(lbl_title)

        self.lbl_existed_path = QLabel()
        layout.addWidget(self.lbl_existed_path)


class ScanTaskItem(QWidget):
    pass


class GUIAnyFile(GUIEntity):
    dj_model = AnyFile
    actions_class = ActionsAnyFileWidget
    field_order = 'filename'
    fields_search = ['directory', 'filename']
    table_class = FilesList
    window_class = FileWindow


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
