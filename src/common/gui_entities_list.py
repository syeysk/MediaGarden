from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QHeaderView, QLabel, QDialog, QAbstractItemView, QWidget
)
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal


class DjangoTableModel(QAbstractTableModel):
    def __init__(self, dj_model, field_names, queryset=None, func_get_value=None):
        super().__init__()
        self.dj_model = dj_model
        self.field_names = field_names
        self._headers = []
        self._data = []
        self.entities = []
        self.queryset = dj_model.objects if queryset is None else queryset 
        self.func_get_value = func_get_value
        for name in field_names:
            if name == 'id':
                self._headers.append('ID')
            else:
                self._headers.append(dj_model._meta.get_field(name).verbose_name.capitalize())

        self.refresh()

    def refresh(self):
        self.beginResetModel()
        _data = self.queryset.only(*self.field_names)
        self._data = []
        self.entities = []
        for entity in _data:
            self.entities.append(entity)
            row = []
            for name in self.field_names:
                value = getattr(entity, name)
                dj_field = self.dj_model._meta.get_field(name)
                if dj_field.choices:
                    value = dict(dj_field.choices).get(value)

                row.append(self.func_get_value(entity, name, value) if self.func_get_value else value)

            self._data.append(row)

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):  # TODO: узнать, что это за аргумент parent
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.field_names)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]

        return None


class EntitiesList(QWidget):
    tag_count_changed = pyqtSignal(object)
    signal_open_entity = pyqtSignal(object)
    signal_add_entity = pyqtSignal()
    signal_delete_entity = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.open_edit_dialog)

        self.title_label = QLabel()
        self.title_label.setStyleSheet('font-size: 20px; font-weight: bold;')

        btn_add = QPushButton('Добавить')
        btn_add.clicked.connect(self.open_add_dialog)
        btn_delete = QPushButton('Удалить')
        btn_delete.clicked.connect(self.open_delete_dialog)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_delete)
        layout.addLayout(header_layout)
        layout.addWidget(self.table)
        # layout.addWidget(btn_add, alignment=Qt.AlignmentFlag.AlignHCenter)
    
    def refresh(self):
        self.table.model().refresh()
    
    def open_edit_dialog(self, index):
        entity = self.table.model().entities[index.row()]
        self.signal_open_entity.emit(entity)

    def open_add_dialog(self):
        self.signal_add_entity.emit()

    def open_delete_dialog(self, _):
        index = self.table.currentIndex()
        index_row = index.row()
        if index_row > -1:
            entity = self.table.model().entities[index.row()]
            self.signal_delete_entity.emit(entity)

    def set_model(self, gui_model, *args):
        model = DjangoTableModel(gui_model.dj_model, gui_model.table_fields, *args)
        self.title_label.setText(str(gui_model.dj_model._meta.verbose_name_plural))
        self.table.setModel(model)
