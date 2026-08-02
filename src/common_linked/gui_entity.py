from common.gui_entity import GUIEntity
from common_linked.gui_entity_windows import LinkedObjectWindow


class GUILinkedObject(GUIEntity):
    window_class = LinkedObjectWindow

    def __init__(self, dj_model, table_fields, *args, **kwargs):
        self.dj_model = dj_model
        self.table_fields = table_fields
        super().__init__(*args, **kwargs)

