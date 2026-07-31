from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QHBoxLayout, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel
)

from common.gui_entities_list import EntitiesList
from common.gui_entity_types import EntityTypesWidget
from common.gui_tags import TagsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 2, screen.height() - 30)
        self.actions_widget = None
        self.table_widget = None
        self.current_gui_model = None

        self.central_widget = QSplitter()
        self.setCentralWidget(self.central_widget)

        # central_widget = QWidget()
        # self.setCentralWidget(central_widget)
        # self.central_widget = QHBoxLayout(central_widget)

        # Левая панель

        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        self.central_widget.addWidget(left_panel)

        left_layout = QVBoxLayout()

        entity_types = EntityTypesWidget(self.gui_models)
        entity_types.selected_entity_type.connect(self.change_table)
        left_layout.addWidget(entity_types)

        self.actions_holder = QVBoxLayout()
        left_layout.addLayout(self.actions_holder)

        left_layout.addSpacing(15)

        self.tags_widget = TagsWidget()
        self.tags_widget.tag_status_changed.connect(self.update_table)
        left_layout.addWidget(self.tags_widget)

        left_panel.setLayout(left_layout)

        # Правая панель

        right_panel = QWidget()
        right_panel.setFixedWidth(900)
        right_layout = QVBoxLayout(right_panel)

        ## Поиск

        top_layout = QHBoxLayout()
        btn_clear = QPushButton('x')
        btn_search = QPushButton('Найти')
        self.field_search = QLineEdit()
        lbl_search_title = QLabel('Найдено: ')
        self.lbl_search_count = QLabel()

        self.field_search.textChanged.connect(self.update_table)
        btn_clear.clicked.connect(lambda: self.field_search.setText(''))
        btn_search.clicked.connect(self.update_table)

        top_layout.addWidget(btn_clear)
        top_layout.addWidget(self.field_search)
        top_layout.addWidget(btn_search)
        top_layout.addWidget(lbl_search_title)
        top_layout.addWidget(self.lbl_search_count)
        top_layout.addStretch()

        right_layout.addLayout(top_layout)
        self.central_widget.addWidget(right_panel)

        self.table_holder = QVBoxLayout()
        right_layout.addLayout(self.table_holder)

        self.entity_types = entity_types

    def update_tags(self):
        self.tags_widget.build_tags(self.current_gui_model.dj_model)

    def update_table(self):
        pass

    def update_actions(self):
        if self.actions_widget:
            self.actions_holder.removeWidget(self.actions_widget)
            self.actions_widget.deleteLater()

        self.actions_widget = None
        actions_class = self.current_gui_model.actions_class
        if actions_class:
            self.actions_widget = actions_class(self)
            self.actions_holder.addWidget(self.actions_widget)

    def update_table(self):
        queryset = self.current_gui_model().select_rows(
            self.tags_widget.checked_tags_id or None,
            self.field_search.text(),
        )
        self.lbl_search_count.setText(str(queryset.count()))
        if self.current_gui_model.table_class:
            self.table_widget.set_data(queryset)
        else:
            self.table_widget.set_model(self.current_gui_model, queryset)

    def change_table(self, gui_model):
        self.current_gui_model = gui_model

        if self.table_widget:
            self.table_holder.removeWidget(self.table_widget)
            self.table_widget.deleteLater()

        table_class = gui_model.table_class
        if table_class:
            self.table_widget = table_class(self)
            self.table_widget.tag_count_changed.connect(self.tags_widget.on_changed_count)
            self.table_widget.double_clicked.connect(self.on_item_clicked)
        else:
            self.table_widget = EntitiesList()

        self.table_holder.addWidget(self.table_widget, stretch=1)
        self.update_table()
        self.update_tags()
        self.update_actions()

    def on_item_clicked(self, dj_entity):
        window = self.current_gui_model.window_class(dj_entity)
        window.exec()
