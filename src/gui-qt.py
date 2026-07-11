import os
import sys

import django
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableView, QHeaderView, QLabel, QDialog, QMessageBox, QSplitter,
    QLineEdit, QDialogButtonBox, QAbstractItemView, QComboBox, QScrollArea, QCheckBox, QTextEdit,
    QTreeView, QTreeWidgetItem, QListView, QAbstractScrollArea, QStyledItemDelegate
)
from PyQt6.QtGui import QIntValidator, QIcon, QStandardItemModel, QStandardItem, QPalette
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal, QAbstractListModel

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from scanner import LibraryStorage
from utils import open_file_with_default_program

from django.conf import settings


class CheckboxDelegate(QStyledItemDelegate):
    toggled = pyqtSignal(QModelIndex, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        button = QCheckBox(parent=parent)
        button.clicked.connect(lambda: self.on_toggle(index, button.isChecked()))        
        return button

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def on_toggle(self, index, is_checked):
        self.toggled.emit(index, is_checked)


class TagsWidget(QWidget):
    tag_status_changed = pyqtSignal()
    new_tag_name = 'новый тег'

    def __init__(self, lib_storage, parent=None):
        super().__init__(parent)
        self.lib_storage = lib_storage
        layout = QVBoxLayout(self)
        self.rows = {}
        self.checked_tags_id = set()

        # Tags tree

        tree_view = QTreeView()
        self.delegate = CheckboxDelegate(tree_view)
        self.delegate.toggled.connect(self.on_toggled)
        tree_view.setItemDelegateForColumn(1, self.delegate)
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

        model.rowsInserted.connect(self.activate_buttons)
        self.activate_buttons()

    def activate_buttons(self, parent_index=QModelIndex(), start=0, end=0):
        # Говорим QTreeView открыть живые виджеты для строк
        # Благодаря виртуализации Qt, они будут создаваться только для того, что на экране
        model = self.model
        for row in range(model.rowCount(parent_index)):
            idx = model.index(row, 1, parent_index)
            self.tree_view.openPersistentEditor(idx)
            # Рекурсивно для вложенных строк, если они развернуты
            if model.hasChildren(idx):
                self.activate_buttons(idx)

    def build_tags(self, parent_id=None, parent_row=None):
        parents = []
        for dj_tag in self.lib_storage.db.select_tags(parent_id):
            row = [
                QStandardItem(dj_tag.name),
                QStandardItem(),
                QStandardItem(str(dj_tag.files.count())),
            ]
            row[0].setData(dj_tag)
            parents.append((dj_tag.pk, row))
            if parent_row:
                parent_row[0].appendRow(row)
            else:
                self.model.appendRow(row)

            self.rows[dj_tag.pk] = row

        for next_parent_id, row in parents:
            self.build_tags(next_parent_id, row)
        
        if parent_row is None:
            self.tree_view.expandAll()
    
    def on_changed_count(self, dj_tag):
        row = self.rows[dj_tag.pk]
        row[2].setText(str(dj_tag.files.count()))

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
        # TODO: раскомментировать
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
        # TODO: раскомментировать
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
                
                # TODO: раскомментировать
                # dj_tag.delete()
                # self.checked_tags_id.remove(dj_tag.pk)

    def on_toggled(self, index, is_checked):
        index = self.model.index(index.row(), 0, index.parent())
        item = self.model.itemFromIndex(index)
        dj_tag = item.data()
        if is_checked:
            self.checked_tags_id.add(dj_tag.pk)
        else:
            self.checked_tags_id.remove(dj_tag.pk)

        self.tag_status_changed.emit()


class TagWidget(QWidget):
    unassigned = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        tag_layout = QHBoxLayout(self)
        self.lbl_tag_name = QLabel()
        tag_layout.addWidget(self.lbl_tag_name)
        btn_tag_delete = QPushButton('x')
        btn_tag_delete.clicked.connect(self.unassign_from_file)
        tag_layout.addWidget(btn_tag_delete)
        self.dj_tag = None

    def set_data(self, dj_tag):
        self.lbl_tag_name.setText(dj_tag.name)
        self.dj_tag = dj_tag

    def unassign_from_file(self):
        self.unassigned.emit(self.dj_tag)


class FileCardWidget(QWidget):
    tag_unassigned = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        # self.setStyleSheet('QVBoxLayout {border: 1px solid white;}')

        data_layout = QHBoxLayout()
        self.lbl_filename = QLabel()
        self.lbl_directory = QLabel()
        descr_layout = QVBoxLayout()
        descr_layout.addWidget(self.lbl_filename)
        descr_layout.addWidget(self.lbl_directory)

        btn_open_file = QPushButton('Open')
        btn_open_file.clicked.connect(self.open_file)
        btn_open_directory = QPushButton('Open')
        btn_open_directory.clicked.connect(self.open_directory)
        btns_layout = QVBoxLayout()
        btns_layout.addWidget(btn_open_file)
        btns_layout.addWidget(btn_open_directory)

        data_layout.addLayout(descr_layout, stretch=1)
        data_layout.addLayout(btns_layout)

        layout.addLayout(data_layout)

        self.tags_layout = QHBoxLayout()
        self.tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(self.tags_layout)

        # Фиксируем высоту одной строки для точных расчетов прокрутки
        self.setFixedHeight(120)
        self.widgets: QHBoxLayout = []
        self.dj_file = None

    def update_data(self, dj_file):
        self.dj_file = dj_file
        self.lbl_filename.setText(dj_file.filename)
        self.lbl_directory.setText(dj_file.directory)

        for tag_widget in self.widgets:
           tag_widget.hide()

        for tag_index, dj_tag in enumerate(dj_file.tags.order_by('name')):
            if tag_index < len(self.widgets):
                tag_widget = self.widgets[tag_index]
                tag_widget.set_data(dj_tag)
                tag_widget.show()
            else:
                tag_widget = TagWidget()
                tag_widget.unassigned.connect(self.unassign_tag_from_file)
                tag_widget.set_data(dj_tag)
                self.tags_layout.addWidget(tag_widget)
                self.widgets.append(tag_widget)

    def unassign_tag_from_file(self, dj_tag):
        #self.dj_file.tags.remove(self.dj_tag)  # TODO: раскомментировать
        self.update_data(self.dj_file)
        self.tag_unassigned.emit(dj_tag)
    
    def open_directory(self):
        open_file_with_default_program(self.dj_file.absdirpath)
    
    def open_file(self):
        open_file_with_default_program(self.dj_file.abspath)


class FilesWidgetList(QAbstractScrollArea):
    tag_count_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.queryset = None      # Здесь хранятся только сырые данные (хоть 100 000 элементов)
        self.visible_widgets = [] # Список из ~20 живых виджетов
        self.row_height = 120      # Должна совпадать с ItemWidget.setFixedHeight
        bg_color = self.palette().color(QPalette.ColorRole.Window)
        self.setStyleSheet('border: none;')
        self.setStyleSheet('QAbstractScrollArea {border: initial; background-color: initial;}')
        self.viewport().setStyleSheet(f'background-color: {bg_color.name()};')

        # Контейнер, внутри которого будут физически двигаться наши 20 виджетов
        self.viewport_container = QWidget(self.viewport())
        
        # Настройка скроллбаров
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.verticalScrollBar().valueChanged.connect(self.update_widgets_position)

    def set_data(self, queryset):
        """Загрузка данных в список"""
        self.queryset = queryset
        
        # Удаляем старые виджеты, если они были
        for w in self.visible_widgets:
            w.deleteLater()

        self.visible_widgets.clear()
        
        # Вычисляем, сколько виджетов помещается на экране + 2 запасных сверху/снизу
        total_count = self.queryset.count()
        visible_count = (self.viewport().height() // self.row_height) + 2
        visible_count = min(visible_count, total_count)
        
        # Создаем минимально необходимое количество виджетов
        for _ in range(max(20, visible_count)): # Минимум 20 для запаса при ресайзе
            w = FileCardWidget(self.viewport_container)
            w.tag_unassigned.connect(self.tag_unassigned)
            w.show()
            self.visible_widgets.append(w)
            
        # Обновляем максимальное значение скроллбара
        total_height = total_count * self.row_height
        self.verticalScrollBar().setRange(0, max(0, total_height - self.viewport().height()))
        self.verticalScrollBar().setPageStep(self.viewport().height())
        
        self.update_widgets_position()
    
    def tag_unassigned(self, dj_tag):
        self.tag_count_changed.emit(dj_tag)
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total_count = self.queryset.count()
        # Пересчитываем размеры контейнера при изменении окна
        self.viewport_container.setGeometry(0, 0, self.viewport().width(), total_count * self.row_height)
        if total_count:
            self.set_data(self.queryset) # Пересоздаем виджеты под новый размер экрана

    def update_widgets_position(self):
        """Магия переиспользования: двигает виджеты и меняет в них текст"""
        total_count = self.queryset.count()
        if not total_count:
            return
        
        scroll_value = self.verticalScrollBar().value()

        # Находим индекс первой видимой строки
        first_visible_idx = scroll_value // self.row_height

        # Смещение внутри контейнера для плавной прокрутки
        offset = scroll_value % self.row_height  # TODO: удалить?
        
        # Двигаем сам контейнер вверх относительно viewport
        self.viewport_container.move(0, -scroll_value)
        
        # Перераспределяем наши 20 виджетов по экрану
        for i, widget in enumerate(self.visible_widgets):
            current_row = first_visible_idx + i
            if current_row < total_count:
                # Если строка существует, наполняем виджет данными и сдвигаем его на нужное место
                dj_file = self.queryset[current_row]
                widget.update_data(dj_file)
                
                # Физически перемещаем виджет на его координату по Y
                widget.move(0, current_row * self.row_height)
                widget.resize(self.viewport().width(), self.row_height)
                widget.show()
            else:
                # Если данные кончились (низ списка), прячем лишние виджеты
                widget.hide()


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
        self.tags_widget.tag_status_changed.connect(self.update_books_list)
        self.tags_widget.build_tags()
        left_layout.addWidget(self.tags_widget)

        central_widget.addWidget(left_panel)

        # Правая панель

        right_panel = QWidget()
        right_panel.setFixedWidth(900)
        right_layout = QVBoxLayout(right_panel)

        top_layout = QHBoxLayout()
        self.field_search = QLineEdit()
        self.field_search.textChanged.connect(self.update_books_list)
        top_layout.addWidget(self.field_search)
        btn_search = QPushButton('Найти')
        btn_search.clicked.connect(self.update_books_list)
        top_layout.addWidget(btn_search)
        lbl_search_title = QLabel('Найдено: ')
        top_layout.addWidget(lbl_search_title)
        self.lbl_search_count = QLabel()
        top_layout.addWidget(self.lbl_search_count)
        top_layout.addStretch()

        right_layout.addLayout(top_layout)

        self.files_widget = FilesWidgetList(self)
        self.files_widget.tag_count_changed.connect(self.tags_widget.on_changed_count)
        right_layout.addWidget(self.files_widget, stretch=1)
        self.update_books_list()
        central_widget.addWidget(right_panel)
    
    def update_books_list(self):
        queryset = self.lib_storage.db.select_rows_new(
            self.tags_widget.checked_tags_id or None,
            self.field_search.text(),
        )
        self.lbl_search_count.setText(str(queryset.count()))
        self.files_widget.set_data(queryset)
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
