from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QAbstractScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPalette

from common.gui_tags import TaggedWidget
from utils import open_file_with_default_program


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


class FileCardWidget(TaggedWidget):
    double_clicked = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        # self.setStyleSheet('QVBoxLayout {border: 1px solid white;}')
        # self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # self.setStyleSheet('background-color: white;')

        # palette = self.palette()
        # palette.setColor(QPalette.ColorRole.Base, QColor('blue'))
        # self.setPalette(palette)
        # self.setAutoFillBackground(True)

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
        self.dj_entity = None
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.dj_entity)
        
        super().mouseDoubleClickEvent(event)

    def update_data(self, dj_entity):
        self.dj_entity = dj_entity
        self.lbl_filename.setText(dj_entity.filename)
        self.lbl_directory.setText(dj_entity.directory)

        for tag_widget in self.widgets:
           tag_widget.hide()

        for tag_index, dj_tag in enumerate(dj_entity.tags.order_by('name')):
            if tag_index < len(self.widgets):
                tag_widget = self.widgets[tag_index]
                tag_widget.set_data(dj_tag)
                tag_widget.show()
            else:
                tag_widget = TagWidget()
                tag_widget.unassigned.connect(self.unassign_tag)
                tag_widget.set_data(dj_tag)
                self.tags_layout.addWidget(tag_widget)
                self.widgets.append(tag_widget)
    
    def open_directory(self):
        open_file_with_default_program(self.dj_entity.absdirpath)
    
    def open_file(self):
        open_file_with_default_program(self.dj_entity.abspath)


# TODO: Почитать, чем это лучше QListView? Возможно, переделать на QListView
class FilesList(QAbstractScrollArea):
    tag_count_changed = pyqtSignal(object)
    double_clicked = pyqtSignal(object)

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

    def on_double_clicked(self, dj_entity):
        self.double_clicked.emit(dj_entity)

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
            w.tag_unassigned.connect(self.on_tag_unassigned)
            w.tag_assigned.connect(self.on_tag_assigned)
            w.double_clicked.connect(self.on_double_clicked)
            w.show()
            self.visible_widgets.append(w)
            
        # Обновляем максимальное значение скроллбара
        total_height = total_count * self.row_height
        self.verticalScrollBar().setRange(0, max(0, total_height - self.viewport().height()))
        self.verticalScrollBar().setPageStep(self.viewport().height())
        
        self.update_widgets_position()
    
    def on_tag_unassigned(self, dj_tag):
        self.tag_count_changed.emit(dj_tag)

    def on_tag_assigned(self, dj_tag):
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
