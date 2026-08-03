from django.core.exceptions import FieldDoesNotExist
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QTreeView, QStyledItemDelegate, QStyle, QComboBox, QDialog, QListView,
    QStyleOptionButton, QApplication,
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDrag, QPainter, QPalette
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal, QMimeData, QThread, pyqtSlot, QObject

from mediagarden.exporters import CSVExporter, MarkdownExporter
from mediagarden.models import AnyFile
from mediagarden.scanner import (
    LibraryStorage, STATUS_NEW, STATUS_MOVED, STATUS_RENAMED, STATUS_MOVED_AND_RENAMED,
    STATUS_UNTOUCHED, STATUS_DELETED, STATUS_DUPLICATE,
)


class ExportWorker(QObject):
    finished = pyqtSignal()
    progress_count_exported_files = pyqtSignal(int, int, int)

    def __init__(self, lib_storage, exporter):
        super().__init__()
        self.lib_storage = lib_storage
        self.exporter = exporter

    @pyqtSlot()
    def run_task(self):
        try:
            self.lib_storage.export_db(
                self.exporter,
                self.progress_count_exported_files.emit,
            )
        except Exception as error:
            print(error)

        self.finished.emit()


class ImportWorker(QObject):
    finished = pyqtSignal()
    progress_count_imported_files = pyqtSignal(int)

    def __init__(self, lib_storage):
        super().__init__()
        self.lib_storage = lib_storage

    @pyqtSlot()
    def run_task(self):
        try:
            self.lib_storage.import_csv_to_db(
                self.progress_count_imported_files.emit,
            )
            print('Импорт завершён')
        except Exception as error:
            print(error)

        self.finished.emit()


class ScanWorker(QObject):
    finished = pyqtSignal()
    progress_count_scanned_files = pyqtSignal(int)
    progress_current_file = pyqtSignal(str)
    add_file_task_card = pyqtSignal(str, AnyFile, AnyFile)

    def __init__(self, lib_storage):
        super().__init__()
        self.lib_storage = lib_storage

    @pyqtSlot()
    def run_task(self):
        try:
            self.lib_storage.scan_to_db(
                progress_count_scanned_files=self.progress_count_scanned_files.emit,
                progress_current_file=self.progress_current_file.emit,
                func=self.add_file_task_card.emit,
            )
            print('Сканирование завершено')
        except Exception as error:
            print(error)

        self.finished.emit()


class ExportWindow(QDialog):
    def __init__(self, lib_storage: LibraryStorage, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Export')
        self.lib_storage = lib_storage

        layout = QVBoxLayout(self)

        TITLE_MARKDOWN = 'Markdown'
        TITLE_CSV = 'CSV'

        self.field_export_type = QComboBox()
        self.field_export_type.addItem(TITLE_MARKDOWN, MarkdownExporter)
        self.field_export_type.addItem(TITLE_CSV, CSVExporter)
        self.field_export_type.setCurrentText(TITLE_MARKDOWN)
        title_export_type = QLabel('Экспортировать как:')
        layout_export_type = QHBoxLayout()
        layout_export_type.addWidget(title_export_type)
        layout_export_type.addWidget(self.field_export_type)
        layout.addLayout(layout_export_type)

        layout_index_of_current_row = QHBoxLayout()
        layout_count_rows = QHBoxLayout()
        layout_current_page = QHBoxLayout()
        layout.addLayout(layout_count_rows)
        layout.addLayout(layout_index_of_current_row)
        layout.addLayout(layout_current_page)

        title_count_rows = QLabel('Всего книг:')
        title_index_of_current_row = QLabel('Экспортировано книг:')
        title_current_page = QLabel('Создано страниц-заметок:')

        self.lbl_count_rows = QLabel('-')
        self.lbl_index_of_current_row = QLabel('-')
        self.lbl_current_page = QLabel('-')
        layout_count_rows.addWidget(title_count_rows)
        layout_count_rows.addWidget(self.lbl_count_rows)
        layout_index_of_current_row.addWidget(title_index_of_current_row)
        layout_index_of_current_row.addWidget(self.lbl_index_of_current_row)
        layout_current_page.addWidget(title_current_page)
        layout_current_page.addWidget(self.lbl_current_page)

        btn_start = QPushButton('Начать экспорт')
        btn_start.clicked.connect(self.start_export)
        layout.addWidget(btn_start)

    def start_export(self):
        self.worker = ExportWorker(self.lib_storage, self.field_export_type.currentData())
        self.worker.progress_count_exported_files.connect(self.progress_count_exported_files)

        # TODO: вынести в функцию
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_task)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def progress_count_exported_files(self, index_of_current_row: int, count_rows: int, current_page: int):
        self.lbl_index_of_current_row.setText(str(index_of_current_row))
        self.lbl_count_rows.setText(str(count_rows))
        self.lbl_current_page.setText(str(current_page))        


class ImportWindow(QDialog):
    finished = pyqtSignal()

    def __init__(self, lib_storage: LibraryStorage, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Import')
        self.lib_storage = lib_storage

        layout = QVBoxLayout(self)

        layout_progress = QHBoxLayout()
        self.lbl_index_current_row = QLabel('-')
        layout_progress.addWidget(QLabel('Импортировано книг:'))
        layout_progress.addWidget(self.lbl_index_current_row)

        layout.addLayout(layout_progress)

        btn_start = QPushButton('Начать импорт')
        btn_start.clicked.connect(self.start_import)
        layout.addWidget(btn_start)

    def progress_count_imported_files(self, index_of_current_row: int):
        self.lbl_index_current_row.setText(str(index_of_current_row))

    def start_import(self):
        self.worker = ImportWorker(self.lib_storage)
        self.worker.progress_count_imported_files.connect(self.progress_count_imported_files)
        self.worker.finished.connect(self.finished.emit)

        # TODO: вынести в функцию
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_task)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


class ItemData:
    def __init__(self, title, description):
        self.title = title
        self.description = description


class ScanCardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_width = 80
        self.button_height = 25
        self.padding = 10

    def sizeHint(self, option, index):
        return QSize(200, 60)  # Высота одной строки

    def _get_button_rect(self, option):
        """Вычисляет координаты кнопки внутри элемента строки"""
        # Кнопка прижата к правому краю с отступами
        x = option.rect.right() - self.button_width - self.padding
        y = option.rect.top() + (option.rect.height() - self.button_height) // 2
        return QStyleOptionButton().rect.__class__(x, y, self.button_width, self.button_height)


    def paint(self, painter, option, index: QModelIndex):
        """Этот метод вызывается автоматически для отрисовки ячейки в реальном времени."""
        # 1. Рисуем стандартный фон выделения строки
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        item_data: ItemData = index.data(Qt.ItemDataRole.UserRole)
        item_data = ItemData('title', 'desscr')
        if not item_data:
            return

        painter.save()

        # 2. Отрисовка текста (Labels)
        painter.setPen(option.palette.color(QPalette.ColorRole.Text))
        # Заголовок (жирный)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            option.rect.adjusted(self.padding, 10, -self.button_width - 20, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            item_data.title,
        )
        
        # Описание (обычный шрифт)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(
            option.rect.adjusted(self.padding, 30, -self.button_width - 20, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            item_data.description,
        )

        # 3. Отрисовка "кнопки" через встроенный стиль ОС
        btn_option = QStyleOptionButton()
        btn_option.rect = self._get_button_rect(option)
        btn_option.text = "Клик!"
        btn_option.state = QStyle.StateFlag.State_Enabled
        
        # Проверяем, находится ли мышь над кнопкой (эффект hover)
        hover_pos = option.widget.property("hover_pos")
        if hover_pos and btn_option.rect.contains(hover_pos):
            print('bbb')
            btn_option.state |= QStyle.StateFlag.State_MouseOver
        
        if option.state & QStyle.StateFlag.State_MouseOver:
            print('aaa')

        style.drawControl(QStyle.ControlElement.CE_PushButton, btn_option, painter, option.widget)
        painter.restore()

        # Получаем данные из модели (ожидаем число от 0 до 100)
        # value_data = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        
        # if value_data is not None:
        # try:
        #     progress = 10#int(value_data)
            
        #     # Инициализируем стиль для ProgressBar
        #     opts = QStyleOption()
        #     opts.rect = option.rect # Задаем границы ячейки
        #     opts.minimum = 0
        #     opts.maximum = 100
        #     opts.progress = progress
        #     opts.text = f"{progress}%"
        #     opts.textVisible = True
            
        #     # Рисуем ProgressBar стандартными средствами текущей темы ОС
        #     QApplication.style().drawControl(
        #         QStyle.ControlElement.CE_PushButton, opts, painter
        #     )
        #     return  # Завершаем метод, чтобы базовый класс не рисовал текст поверх
        # except ValueError:
        #     pass # Если данные не числовые, сработает дефолтная отрисовка ниже
                
        # # Для всех остальных случаев используем стандартную отрисовку
        # super().paint(painter, option, index)

    # def createEditor(self, parent, option, index):
    #     return QPushButton('button', parent=parent)
    #     card_type = index.data(ScanCardTypeRole)
    #     print(card_type, index.row())
    #     if card_type == STATUS_NEW:
    #         return ScanTaskNewWidget(parent=parent)
    #     elif card_type == STATUS_DELETED:
    #         return ScanTaskDeletedWidget(parent=parent)
    #     elif card_type in {STATUS_MOVED, STATUS_RENAMED, STATUS_MOVED_AND_RENAMED}:
    #         return ScanTaskMovedWidget(parent=parent)
    #     elif card_type == STATUS_DUPLICATE:
    #         return ScanTaskDuplicateWidget(parent=parent)
    #     elif card_type == STATUS_UNTOUCHED:
    #         return ScanTaskUntouchedWidget(parent=parent)

    # def setEditorData(self, editor, index):
    #     value = index.data(Qt.ItemDataRole.DisplayRole)
    #     card_type = index.data(ScanCardTypeRole)

    #     if card_type == STATUS_NEW:
    #         editor.setText(str(value))
    #     elif card_type == STATUS_DELETED:
    #         editor.setText(str(value))
    
    # def setModelData(self, editor, model, index):
    #     print('setModelData', editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        return editor.setGeometry(option.rect)
        # return super().updateEditorGeometry(editor, option, index)


class ScanWindow(QDialog):
    finished = pyqtSignal()

    def __init__(self, lib_storage: LibraryStorage, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Scaning')
        self.lib_storage = lib_storage

        layout = QVBoxLayout(self)

        layout_statistic = QVBoxLayout()
        layout_row_scanned = QHBoxLayout()
        layout_row_new = QHBoxLayout()
        layout_row_buttons = QHBoxLayout()

        self.lbl_count_scanned = QLabel('-')
        self.lbl_new = QLabel('-')
        self.lbl_current_path = QLabel('')
        layout_row_scanned.addWidget(QLabel('Сканировано:'))
        layout_row_scanned.addWidget(self.lbl_count_scanned)
        layout_row_new.addWidget(QLabel('Новые:'))
        layout_row_new.addWidget(self.lbl_new)

        btn_start = QPushButton('Сканировать')
        btn_start.clicked.connect(self.start_scan)
        btn_stop = QPushButton('Остановить')
        btn_stop.clicked.connect(self.stop_scan)
        layout_row_buttons.addWidget(btn_start)
        layout_row_buttons.addWidget(btn_stop)

        layout_statistic.addLayout(layout_row_scanned)
        layout_statistic.addLayout(layout_row_new)
        layout_statistic.addWidget(self.lbl_current_path)
        layout.addLayout(layout_statistic)
        layout.addLayout(layout_row_buttons)

        cards_list = QListView()
        cards_list.resize(300, 400)
        cards_model = QStandardItemModel()#ScanCardListModel()
        cards_model.flags = lambda x: Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        self.delegate = ScanCardDelegate()
        cards_list.setModel(cards_model)
        cards_list.setItemDelegateForColumn(0, self.delegate)
        cards_list.setItemDelegate(self.delegate)
        cards_list.setItemDelegateForRow(0, self.delegate)
        cards_list.setEditTriggers(QListView.EditTrigger.DoubleClicked | QListView.EditTrigger.SelectedClicked)
        layout.addWidget(cards_list)

        self.count_new = 0
        cards_model.setItem(0, QStandardItem())
        cards_model.setItem(1, QStandardItem())

    def progress_count_scanned_files(self, count_scanned_files: int):
        self.lbl_count_scanned.setText(str(count_scanned_files))

    def progress_current_file(self, full_path: str):
        self.lbl_current_path.setText(full_path)
    
    def add_file_task_card(self, status: str, inserted_anyfile: AnyFile, existed_anyfile: AnyFile):
        if status == STATUS_UNTOUCHED:
            return

    def start_scan(self):
        self.worker = ScanWorker(self.lib_storage)
        self.worker.progress_count_scanned_files.connect(self.progress_count_scanned_files)
        self.worker.progress_current_file.connect(self.progress_current_file)
        self.worker.add_file_task_card.connect(self.add_file_task_card)
        self.worker.finished.connect(self.finished.emit)

        # TODO: вынести в функцию
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_task)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def stop_scan(self):
        pass  # TODO: реализовать


class ActionsAnyFileWidget(QWidget):
    def __init__(self, main_window, parent=None):
        # TODO: убрать padding или margin со всех таких виджетов!
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.lib_storage = LibraryStorage()
        self.main_window = main_window

        btn_scan = QPushButton('Сканировать')
        btn_scan.clicked.connect(self.on_click_scan)
        layout.addWidget(btn_scan)

        btn_scan_extern = QPushButton('Сканировать внешнее')
        btn_scan_extern.setDisabled(True)
        layout.addWidget(btn_scan_extern)

        layout.addSpacing(15)

        btn_export = QPushButton('Экспортировать в заметки')
        btn_export.clicked.connect(self.on_click_export)
        layout.addWidget(btn_export)
        btn_import = QPushButton('Импортировать из CSV')
        btn_import.clicked.connect(self.on_click_import)
        layout.addWidget(btn_import)

    def on_click_export(self):
        window = ExportWindow(self.lib_storage)
        window.exec()

    def on_click_import(self):
        window = ImportWindow(self.lib_storage)
        window.finished.connect(self.on_finished_import)
        window.exec()
    
    def on_finished_import(self):
        self.main_window.update_tags()
        self.main_window.update_table()
    
    def on_click_scan(self):
        window = ScanWindow(self.lib_storage)
        window.finished.connect(self.update_books_list)
        window.exec()
