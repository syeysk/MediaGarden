from PyQt6.QtWidgets import QVBoxLayout

from common.gui_entity_windows import EntityWindow


class LinkedObjectWindow(EntityWindow):
    links = []

    def build_form(self):
        layout = QVBoxLayout()
        for field in self.dj_model._meta.fields:
            if field.name == 'id':
                continue

            field_name = field.name
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout