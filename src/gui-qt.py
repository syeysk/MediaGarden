import os
import sys

import django
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableView, QHeaderView, QLabel, QDialog, QMessageBox, QSplitter,
    QLineEdit, QDialogButtonBox, QAbstractItemView, QComboBox, QScrollArea, QCheckBox, QTextEdit,
    QTreeView, QTreeWidgetItem,
)
from PyQt6.QtGui import QIntValidator, QIcon, QStandardItemModel, QStandardItem
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from scanner import LibraryStorage

from django.conf import settings


class TagsWidget(QWidget):
    new_tag_name = 'новый тег'

    def __init__(self, lib_storage, parent=None):
        super().__init__(parent)
        self.lib_storage = lib_storage

        layout = QVBoxLayout(self)

        # Tags tree

        tree_view = QTreeView()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Тег', '', 'Файлов'])

        tree_view.setModel(model)
        tree_view.setIndentation(10)
        tree_view.setRootIsDecorated(False)
        tree_view.setStyleSheet('QTreeView::branch {width: 0px; image: none;}')
        header = tree_view.header()
        header.resizeSection(0, 200)
        header.resizeSection(1, 20)
        header.resizeSection(2, 50)

        self.model = model
        self.tree_view = tree_view

        layout.addWidget(tree_view, stretch=1)

        # Buttons

        btns_layout = QHBoxLayout()
        btn_delete = QPushButton('-')
        btn_delete.clicked.connect(self.action_delete_tag)
        btns_layout.addWidget(btn_delete)
        btn_add = QPushButton('+')
        btn_add.clicked.connect(self.action_add_tag)
        btns_layout.addWidget(btn_add)
        btn_add_child = QPushButton('+>')
        btn_add_child.clicked.connect(self.action_add_child_tag)
        btns_layout.addWidget(btn_add_child)
        btn_edit = QPushButton('/')
        btns_layout.addWidget(btn_edit)
        layout.addLayout(btns_layout)

    def build_tags(self, parent_id=None, parent_node=None):
        parents = []
        for tag in self.lib_storage.db.select_tags(parent_id):
            node = [
                QStandardItem(tag.name),
                QStandardItem(''),
                QStandardItem(str(tag.files.count())),
            ]
            node[0].setData(tag)
            parents.append((tag.pk, node))
            if parent_node:
                parent_node[0].appendRow(node)
            else:
                self.model.appendRow(node)

        for next_parent_id, node in parents:
            self.build_tags(next_parent_id, node)
        
        if parent_node is None:
            self.tree_view.expandAll()

    def get_selected_item(self) -> tuple[QStandardItem, int] | tuple[None, None]:
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            return self.model.itemFromIndex(index), index.row()

        return None, None

    def action_add_tag(self):
        item, _ = self.get_selected_item()
        node = [
            QStandardItem(self.new_tag_name),
            QStandardItem(''),
            QStandardItem('0'),
        ]
        parent = None
        parent_tag_id = None
        if item:
            parent = item.parent()
            if parent:
                parent_tag_id = parent.data().pk

        (parent or self.model).appendRow(node)
        # dj_tag = self.lib_storage.db.insert_tag(self.new_tag_name, parent_tag_id)
        # node[0].setData(dj_tag)

    def action_add_child_tag(self):
        item, _ = self.get_selected_item()
        node = [
            QStandardItem(self.new_tag_name),
            QStandardItem(''),
            QStandardItem('0'),
        ]
        (item or self.model).appendRow(node)
        # dj_tag = self.lib_storage.db.insert_tag(self.new_tag_name, item.data().pk if item else None)
        # node[0].setData(dj_tag)

    def action_delete_tag(self):
        item, index_row = self.get_selected_item()
        if item:
            dj_tag = item.data()
            count_files = dj_tag.files.count()
            count_child_tags = dj_tag.children.count()
            if not (count_files or count_child_tags):
                parent = item.parent()
                if parent:
                    self.model.removeRow(index_row, parent.index())
                else:
                    self.model.removeRow(index_row)
                
                # dj_tag.delete()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lib_storage = LibraryStorage()

        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 2, screen.height() - 30)
        self.setWindowTitle('MediaGarden - Let\'s your knowledge to grow')
        self.setWindowIcon(QIcon(str(settings.BASE_DIR.parent / 'images/icon.png')))

        central_widget = QSplitter()
        self.setCentralWidget(central_widget)
        #main_layout = QHBoxLayout(central_widget)

        # Левая панель

        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)

        btn_scan = QPushButton('Сканировать')
        left_layout.addWidget(btn_scan)

        btn_scan_extern = QPushButton('Сканировать внешнее')
        btn_scan_extern.setDisabled(True)
        left_layout.addWidget(btn_scan_extern)

        left_layout.addSpacing(15)

        btn_export = QPushButton('Экспортировать в заметки')
        left_layout.addWidget(btn_export)
        btn_import = QPushButton('Импортировать из заметок')
        left_layout.addWidget(btn_import)

        left_layout.addSpacing(15)

        self.tags_widget = TagsWidget(self.lib_storage)
        self.tags_widget.build_tags()
        left_layout.addWidget(self.tags_widget)

        central_widget.addWidget(left_panel)

        # Правая панель

        right_panel = QWidget()

        right_layout = QVBoxLayout(right_panel)

        central_widget.addWidget(right_panel)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
