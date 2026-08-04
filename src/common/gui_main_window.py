from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QHBoxLayout, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTabWidget
)
from PyQt6.QtCore import Qt

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

        # Левая панель

        tab = QTabWidget()
        tab.setMovable(True)
        tab.setTabPosition(QTabWidget.TabPosition.West)
        self.central_widget.addWidget(tab)

        entity_types = EntityTypesWidget(self.gui_models)
        entity_types.selected_entity_type.connect(self.change_table)

        self.actions_holder = QVBoxLayout()
        self.actions_holder.setContentsMargins(0, 0, 0, 0)
        self.actions_holder.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.tags_widget = TagsWidget()
        self.tags_widget.tag_status_changed.connect(self.update_table)

        actions_widget = QWidget()
        actions_widget.setLayout(self.actions_holder)
        tab.addTab(entity_types, 'Types')
        tab.addTab(actions_widget, 'Actions')
        tab.addTab(self.tags_widget, 'Tags')

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
        self.table_widget.set_model(self.current_gui_model, queryset)

    def change_table(self, gui_model):
        self.current_gui_model = gui_model
        if self.table_widget:
            self.table_holder.removeWidget(self.table_widget)
            self.table_widget.deleteLater()

        self.table_widget = gui_model.table_class()
        self.table_widget.tag_count_changed.connect(self.tags_widget.on_changed_count)
        self.table_widget.signal_open_entity.connect(self.on_open_entity)
        self.table_widget.signal_delete_entity.connect(self.on_delete_entity)
        self.table_widget.signal_add_entity.connect(self.on_add_entity)
        self.table_holder.addWidget(self.table_widget, stretch=1)
        self.update_table()
        self.update_tags()
        self.update_actions()

    def on_open_entity(self, dj_entity):
        window = self.current_gui_model.window_class(self.current_gui_model.dj_model, dj_entity)

        def on_saved_entity():
            self.table_widget.refresh()

        window.signal_saved_entity.connect(on_saved_entity)
        window.exec()

    def on_add_entity(self):
        window = self.current_gui_model.window_class(self.current_gui_model.dj_model)

        def on_created_entity(dj_entity):
            self.entity = dj_entity
            self.table_widget.refresh()

        def on_saved_entity():
            self.table_widget.refresh()

        window.signal_created_entity.connect(on_created_entity)
        window.signal_saved_entity.connect(on_saved_entity)

        window.exec()

    def on_delete_entity(self, dj_entity):
        dj_entity.remove()
        self.table_widget.refresh()
