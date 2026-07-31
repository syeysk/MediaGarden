from struct import pack, unpack

from django.core.exceptions import FieldDoesNotExist
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QTreeView, QStyledItemDelegate, QStyle,
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDrag
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal, QMimeData

from common.models import Tag

__all__ = ['TaggedWidget', 'TaggsWidget']


class DragableLabel(QLabel):
    def __init__(self, dj_tag, *args, **kwargs):
        super().__init__(dj_tag.name, *args, **kwargs)
        self.dj_tag = dj_tag

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return
        
        mime_data = QMimeData()
        mime_data.setData('application/x-tag-id', pack('I', self.dj_tag.pk))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)


class TagNameDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def index2dj(self, index):
        model = index.model()
        item = model.itemFromIndex(index)
        return item.data()

    def paint(self, painter, option, index):
        painter.save()
        # if option.state & QStyle.StateFlag.State_MouseOver:
        #     painter.fillRect(option.rect, option.palette.shadow())
        # elif option.state & QStyle.StateFlag.State_Selected:
        #     painter.fillRect(option.rect, option.palette.accent())
        # else:
        #     painter.fillRect(option.rect, option.palette.base())

        dj_tag = self.index2dj(index)
        # dj_tag = index.data(Qt.ItemDataRole.DisplayRole)
        painter.setPen(option.palette.text().color())
        painter.drawText(option.rect.adjusted(5, 0, -5, 0), Qt.AlignmentFlag.AlignVCenter, dj_tag.name)

        painter.restore()
    
    def setEditorData(self, editor, index):
        editor.setText(self.index2dj(index).name)

    # def createEditor(self, parent, option, index):
    #     model = index.model()
    #     item = model.itemFromIndex(index)
    #     dj_tag = item.data()
    #     lbl_title = DragableLabel(dj_tag, parent=parent)
    #     return lbl_title

    # def updateEditorGeometry(self, editor, option, index):
    #     editor.setGeometry(option.rect)


class CheckboxDelegate(QStyledItemDelegate):
    toggled = pyqtSignal(QModelIndex, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        button = QCheckBox(parent=parent)
        button.clicked.connect(lambda: self.on_toggle(index, button.isChecked()))        
        return button

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def on_toggle(self, index, is_checked):
        self.toggled.emit(index, is_checked)


# TODO: Либо передавать модель Tag в аргументе (и для каждой модели будет своя модель с тегами) либо добавить в модель харнение тегов разных моделей
class TagsWidget(QWidget):
    tag_status_changed = pyqtSignal()
    new_tag_name = 'новый тег'
    column_index_name = 0
    column_index_checkbox = 1
    column_index_count = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dj_model = None
        layout = QVBoxLayout(self)
        self.rows = {}
        self.checked_tags_id = set()

        # Tags tree
        tree_view = QTreeView()
        delegate_name = TagNameDelegate(tree_view)
        tree_view.setItemDelegateForColumn(self.column_index_name, delegate_name)
        delegate_checkbox = CheckboxDelegate(tree_view)
        delegate_checkbox.toggled.connect(self.on_toggled)
        tree_view.setItemDelegateForColumn(self.column_index_checkbox, delegate_checkbox)

        model = QStandardItemModel()
        # model.setHorizontalHeaderLabels(['Тег', '', 'Объектов'])
        model.dataChanged.connect(self.on_item_changed)

        tree_view.setModel(model)
        tree_view.setIndentation(10)
        tree_view.setRootIsDecorated(False)
        tree_view.setStyleSheet('QTreeView::branch {width: 0px; image: none;}')
        header = tree_view.header()
        header.resizeSection(self.column_index_name, 200)
        header.resizeSection(self.column_index_checkbox, 20)
        header.resizeSection(self.column_index_count, 50)
        header.setHidden(True)

        self.model = model
        self.tree_view = tree_view

        layout.addWidget(tree_view, stretch=1)

        # Buttons

        btns_layout = QHBoxLayout()
        btn_delete = QPushButton('-')
        btn_delete.clicked.connect(self.action_delete_tag)
        btns_layout.addWidget(btn_delete)
        btn_add = QPushButton('+')
        btn_add.clicked.connect(self.action_add_tag)
        btns_layout.addWidget(btn_add)
        btn_add_child = QPushButton('+>')
        btn_add_child.clicked.connect(self.action_add_child_tag)
        btns_layout.addWidget(btn_add_child)
        layout.addLayout(btns_layout)
    
    def on_item_changed(self, top_left, bottom_right, roles):
        if top_left.column() == self.column_index_name:
            item = self.model.itemFromIndex(top_left)
            new_name = item.text().strip()
            dj_tag = item.data()
            if new_name:
                dj_tag.name = new_name
                # dj_tag.save()  # TODO: раскомментировать
            else:
                item.setText(dj_tag.name)

    def build_tags(self, dj_model, parent_id=None, parent_row=None):
        self.dj_model = dj_model
        try:
            dj_field = dj_model._meta.get_field('tags')
        except FieldDoesNotExist:
            print(f'У django-модели {dj_model.__name__} должно быть поле "tags" для поддержки тегов')
            return

        related_name = dj_field._related_name

        parents = []
        for dj_tag in Tag.objects.filter(parent_id=parent_id, code=self.dj_model.CODE):
            entities = getattr(dj_tag, related_name)
            row = [
                QStandardItem(),
                QStandardItem(),
                QStandardItem(str(entities.count())),
            ]
            row[self.column_index_name].setData(dj_tag)
            row[self.column_index_checkbox].setEditable(False)
            row[self.column_index_count].setEditable(False)
            parents.append((dj_tag.pk, row))
            if parent_row:
                parent_row[self.column_index_name].appendRow(row)
            else:
                self.model.appendRow(row)

            # self.tree_view.openPersistentEditor(row[self.column_index_name].index())
            self.tree_view.openPersistentEditor(row[self.column_index_checkbox].index())
            self.rows[dj_tag.pk] = row

        for next_parent_id, row in parents:
            self.build_tags(dj_model, next_parent_id, row)
        
        if parent_row is None:
            self.tree_view.expandAll()
    
    def on_changed_count(self, dj_tag):
        row = self.rows[dj_tag.pk]
        row[self.column_index_count].setText(str(dj_tag.files.count()))

    def get_selected_item(self) -> tuple[QStandardItem, int] | tuple[None, None]:
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            index = indexes[self.column_index_name]
            return self.model.itemFromIndex(index), index.row()

        return None, None

    def action_add_tag(self):
        item, _ = self.get_selected_item()
        row = [
            QStandardItem(self.new_tag_name),
            QStandardItem(),
            QStandardItem('0'),
        ]
        parent = None
        parent_tag_id = None
        if item:
            parent = item.parent()
            if parent:
                parent_tag_id = parent.data().pk

        dj_tag = Tag(name=self.new_tag_name, parent_id=parent_tag_id, code=self.dj_model.CODE)
        dj_tag.save()
        row[self.column_index_name].setData(dj_tag)
        row[self.column_index_count].setEditable(False)
        (parent or self.model).appendRow(row)

    def action_add_child_tag(self):
        item, _ = self.get_selected_item()
        row = [
            QStandardItem(self.new_tag_name),
            QStandardItem(),
            QStandardItem('0'),
        ]
        dj_tag = Tag(name=self.new_tag_name, parent_id=item.data().pk if item else None, code=self.dj_model.CODE)
        dj_tag.save()
        row[self.column_index_name].setData(dj_tag)
        row[self.column_index_count].setEditable(False)
        (item or self.model).appendRow(row)

    def action_delete_tag(self):
        item, index_row = self.get_selected_item()
        if item:
            dj_tag = item.data()
            count_files = dj_tag.files.count()
            count_child_tags = dj_tag.children.count()
            if not (count_files or count_child_tags):
                parent = item.parent()
                if parent:
                    self.model.removeRow(index_row, parent.index())
                else:
                    self.model.removeRow(index_row)
                
                # TODO: раскомментировать
                # dj_tag.delete()
                # self.checked_tags_id.remove(dj_tag.pk)

    def on_toggled(self, index, is_checked):
        index = self.model.index(index.row(), self.column_index_name, index.parent())
        item = self.model.itemFromIndex(index)
        dj_tag = item.data()
        if is_checked:
            self.checked_tags_id.add(dj_tag.pk)
        else:
            self.checked_tags_id.remove(dj_tag.pk)

        self.tag_status_changed.emit()


class TaggedWidget(QWidget):
    tag_unassigned = pyqtSignal(object)
    tag_assigned = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        mime_data: QMimeData = event.mimeData()
        data: bytearray = mime_data.data('application/x-tag-id')
        if data:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime_data: QMimeData = event.mimeData()
        data: bytearray = mime_data.data('application/x-tag-id')
        if data:
            tag_pk = unpack('I', data)[0]
            dj_tag = Tag(pk=tag_pk)
            dj_tag.refresh_from_db()
            self.dj_entity.tags.add(dj_tag)
            self.update_data(self.dj_entity)
            self.tag_assigned.emit(dj_tag)
            event.acceptProposedAction()
        else:
            event.ignore()

    def unassign_tag(self, dj_tag):
        self.dj_entity.tags.remove(dj_tag)
        self.update_data(self.dj_file)
        self.tag_unassigned.emit(dj_tag)
