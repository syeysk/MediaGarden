from django.db.models import Q

from common.gui_entities_list import EntitiesList
from common_linked.gui_entity import GUILinkedObject
from common_linked.gui_entity_windows import LinkedObjectWindow


class LinkedEntitiesTable(EntitiesList):
    def __init__(self, entity, linking_table, item_slave, *args, fields=list(), **kwargs):
        super().__init__(*args, **kwargs)
        self.table.setFixedHeight(200)
        self.table.setMaximumHeight(200)
        self.table.setMinimumHeight(200)
        self.setContentsMargins(0, 50, 0, 0)

        item_main_model = entity.__class__
        item_main = item_main_model.__name__.lower()
        item_slave_model = linking_table._meta.get_field(item_slave).remote_field.model
        same = item_main_model is item_slave_model

        queryset = linking_table.objects
        if same:
            queryset = queryset.filter(Q(**{item_main: entity}) | Q(**{item_slave: entity}))
        else:
            queryset = queryset.filter(**{item_main: entity})

        self.same = same
        self.item_slave = item_slave
        self.item_main = item_main
        self.entity = entity
        self.linking_table = linking_table

        self.gui_model = GUILinkedObject(linking_table, [item_slave, *fields])
        self.signal_open_entity.connect(self.on_open_entity)
        self.signal_add_entity.connect(self.on_add_entity)
        self.signal_delete_entity.connect(self.on_delete_entity)
        self.set_model(self.gui_model, queryset, self.func_get_value)

    def func_get_value(self, hyper_entity, field_name, field_value):
        if self.same and field_name == self.item_slave and field_value.pk == self.entity.pk:
            return getattr(hyper_entity, self.item_main)
            
        return field_value

    def on_open_entity(self, dj_entity):
        window = LinkedObjectWindow(self.linking_table, dj_entity)
        window.exec()
    
    def on_delete_entity(self, dj_entity):
        dj_entity.delete()
        self.refresh()

    def on_add_entity(self):
        window = LinkedObjectWindow(self.linking_table, preset_values={self.item_main: self.entity})

        def on_added_entity(_):
            window.close()
            self.refresh()

        window.signal_created_entity.connect(on_added_entity)
        window.exec()
