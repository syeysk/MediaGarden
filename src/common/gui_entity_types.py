from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

__all__ = ['EntityTypesWidget']


class EntityTypesWidget(QWidget):
    selected_entity_type = pyqtSignal(object)

    def __init__(self, gui_models, parent=None):
        super().__init__(parent)
        self.dj_model = None
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.dict_gui_button = {}
        self.current_gui_model = gui_models[0] if gui_models else None

        for gui_model in gui_models:
            btn = QPushButton(gui_model.dj_model._meta.verbose_name)
            btn.clicked.connect(self.get_select_function(gui_model))
            layout.addWidget(btn)
            self.dict_gui_button[gui_model] = btn

    def get_select_function(self, gui_model):
        def _f():
            if self.current_gui_model:
                self.dict_gui_button[self.current_gui_model].setEnabled(True)

            self.selected_entity_type.emit(gui_model)
            self.dict_gui_button[gui_model].setEnabled(False)
            self.current_gui_model = gui_model

        return _f

    def select_current(self):
        if self.current_gui_model:
            self.get_select_function(self.current_gui_model)()
