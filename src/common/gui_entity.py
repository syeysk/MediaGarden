from django.db.models import Q, Count

from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import pyqtSignal


class GUIEntity(QDialog):
    dj_model = None
    field_order = 'pk'
    fields_search = []
    actions_class = None
    table_class = None
    window_class = None
    links = tuple()
    saved = pyqtSignal()
    created = pyqtSignal(object)

    # Database

    def _build_queryset(self, tags=None, search=''):
        queryset = self.dj_model.objects
        if search and self.fields_search:
            q_condition = None
            for field_search in self.fields_search:
                kwargs = {f'{field_search}__contains': search}
                q_part = Q(**kwargs)
                if q_condition is None:
                    q_condition = q_part
                else:
                    q_condition |= q_part

            queryset = queryset.filter(q_condition)
        
        if tags:
            queryset = queryset.filter(tags__pk__in=tags).annotate(Count('pk'))

        return queryset

    def select_rows(self, tags=None, search=''):
        return self._build_queryset(tags, search).order_by(self.field_order)
