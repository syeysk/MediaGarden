from django.db.models import Q, Count, ForeignKey, BooleanField, IntegerField, TextField, NOT_PROVIDED

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QMessageBox,
    QLineEdit, QDialogButtonBox, QComboBox, QScrollArea, QCheckBox, QTextEdit, QPushButton
)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import pyqtSignal

from common.gui_entities_list import EntitiesList


class SelectEntitywindow(QDialog):
    model = None

    def __init__(self, gui_model):
        super().__init__(None)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 3, 400)
        self.gui_model = gui_model
        table_view = EntitiesList()
        table_view.signal_open_entity.connect(self.on_select_entity)
        table_view.signal_add_entity.connect(self.on_add_entity)
        table_view.signal_delete_entity.connect(self.on_delete_entity)
        table_view.set_model(self.gui_model)
        self.table_view = table_view

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(table_view)

        self.entity = None
    
    def on_select_entity(self, entity):
        self.entity = entity
        self.close()
    
    def on_delete_entity(self, dj_entity):
        dj_entity.delete()
        self.table_view.refresh()

    def on_add_entity(self):
        window = self.gui_model.window_class(self.gui_model.dj_model)

        def on_created_entity(dj_entity):
            self.entity = dj_entity
            window.close()
            self.close()

        def on_saved_entity():
            window.close()
            self.close()

        window.signal_created_entity.connect(on_created_entity)
        window.signal_saved_entity.connect(on_saved_entity)
        window.exec()


class IntegerQField(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setValidator(QIntValidator())
    
    def value(self):
        text = self.text().strip()
        return int(text) if text else None


class ForeignQField(QWidget):
    entity = None

    def __init__(self, gui_model, entity=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QHBoxLayout()
        self.gui_model = gui_model

        self.btn_select = QPushButton()
        self.btn_select.clicked.connect(self.open_select_window)
        layout.addWidget(self.btn_select)

        self.btn_edit = QPushButton('o')
        self.btn_edit.clicked.connect(self.open_entity_window)
        layout.addWidget(self.btn_edit)

        self.setLayout(layout)
        self.set_entity(entity)
    
    def set_entity(self, entity):
        self.entity = entity
        self.btn_select.setText(str(entity))

    def open_entity_window(self):
        if self.entity:
            if self.gui_model(self.entity).exec() == QDialog.DialogCode.Accepted:
                self.btn_select.setText(str(self.entity))

    def open_select_window(self):
        window = SelectEntitywindow(self.gui_model)
        window.exec()
        if window.entity:
            self.set_entity(window.entity)


class EntityWindow(QDialog):
    DJ2GUI = None
    signal_saved_entity = pyqtSignal()
    signal_created_entity = pyqtSignal(object)

    def __init__(self, dj_model, entity=None, preset_values=None):
        super().__init__(None)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, int(screen.width() / 2.5), screen.height() - 30)
        self.preset_values = preset_values or {}
        self.inputs = {}
        self.dj_model = dj_model#gui_model.dj_model
        self.entity = entity
        self.layout_links = None

        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)

        if not self.DJ2GUI:
            from common.gui_entity import GUIEntity
            self.DJ2GUI = {gui.dj_model: gui for gui in GUIEntity.__subclasses__()}

        layout_form = self.build_form()
        self.layout.addLayout(layout_form)
 
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_save = buttons.addButton('Сохранить', QDialogButtonBox.ButtonRole.ApplyRole)
        btn_save.clicked.connect(self.save)
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        self.set_entity(entity)

        # TODO: вынести в отдельный класс ScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidget(central_widget)

    def set_entity(self, entity):
        self.entity = entity
        title_prefix = 'Редактировать' if entity else 'Добавить'
        self.setWindowTitle(f'{title_prefix}: {self.dj_model._meta.verbose_name}')
        self.populate_form()
        self.build_links()

    def save(self):
        ''' Возвращает True при успешном сохранении, иначе - False '''
        data = self.get_data()
        if self.entity:
            for field, value in data.items():
                setattr(self.entity, field, value)

            try:
                self.entity.save()
            except Exception as e:
                self.show_error('при сохранении', str(e))
                return False

            self.signal_saved_entity.emit()
        else:
            try:
                entity = self.dj_model.objects.create(**data)
            except Exception as e:
                self.show_error('при создании', str(e))
                return False

            self.set_entity(entity)
            self.signal_created_entity.emit(entity)

        return True

    def save_and_close(self):
        if self.save():
            self.accept()

    def show_error(self, description, message):
        QMessageBox.critical(self, f'Ошибка {description}', message)

    def populate_form(self):
        for field_name, field in self.inputs.items():
            dj_field = self.dj_model._meta.get_field(field_name)
            if self.entity:
                value = getattr(self.entity, field_name)
            else:
                if field_name in self.preset_values:
                    value = self.preset_values[field_name]
                else:
                    value = '' if dj_field.default is NOT_PROVIDED else dj_field.default
 
            if isinstance(field, QComboBox):
                field.setCurrentText(dict(dj_field.choices)[value])
            elif isinstance(field, QCheckBox):
                field.setChecked(value)
            elif isinstance(field, ForeignQField):
                field.set_entity(value or None)
            elif isinstance(field, (QLineEdit, QTextEdit)):
                field.setText(str(value))

    def build_field_by_model(self, field_name):
        dj_field = self.dj_model._meta.get_field(field_name)
        verbose = dj_field.verbose_name.capitalize()

        choices = dj_field.choices
        if choices:
            field = QComboBox()
            for choice_value, choice_name in choices:
                field.addItem(choice_name, choice_value)
        elif isinstance(dj_field, ForeignKey):
            field = ForeignQField(self.DJ2GUI[dj_field.remote_field.model])
        elif isinstance(dj_field, BooleanField):
            field = QCheckBox()
        elif isinstance(dj_field, IntegerField):
            field = IntegerQField()
        elif isinstance(dj_field, TextField):
            field = QTextEdit()
            field.setFixedHeight(100)
        else:
            field = QLineEdit()

        self.inputs[field_name] = field
        return QLabel(f'{verbose}:'), field

    def build_row(self, field_name):
        label, edit = self.build_field_by_model(field_name)
        layout_line = QHBoxLayout()
        layout_line.addWidget(label)
        layout_line.addWidget(edit)
        return layout_line

    def get_data(self):
        values = {}
        for field, widget in self.inputs.items():
            if isinstance(widget, IntegerQField):
                values[field] = widget.value()
            elif isinstance(widget, QLineEdit):
                values[field] = widget.text()
            elif isinstance(widget, QTextEdit):
                values[field] = widget.toPlainText()
            elif isinstance(widget, ForeignQField):
                values[field] = widget.entity
            elif isinstance(widget, QCheckBox):
                values[field] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[field] = widget.currentData()
            else:
                print('Unknown type of field:', widget, field)

        return values
    
    def build_form(self):
        raise NotImplementedError

    def build_links(self):
        from common_linked.gui_entities_list import LinkedEntitiesTable  # TODO: так не должно быть
        if self.layout_links:
            self.layout_links.remove()

        self.layout_links = QVBoxLayout()
        if self.entity:
            for link_args, link_kwargs in self.links:
                table = LinkedEntitiesTable(self.entity, *link_args, **link_kwargs)
                self.layout_links.addWidget(table)

        self.layout.addLayout(self.layout_links)
