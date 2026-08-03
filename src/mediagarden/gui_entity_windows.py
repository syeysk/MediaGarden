from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QLabel, QDialog
from PyQt6.QtCore import pyqtSignal

from utils import open_file_with_default_program

from mediagarden.gui_entities_list import FilesList
from common.gui_entity import GUIEntity
from mediagarden.gui_actions import ActionsAnyFileWidget
from mediagarden.models import AnyFile


class FileWindow(QDialog):
    signal_saved_entity = pyqtSignal()
    signal_created_entity = pyqtSignal(object)

    def __init__(self, dj_model, dj_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle('File details')
        self.dj_file = dj_file

        layout = QVBoxLayout(self)

        lbl_filename = QLabel(dj_file.filename)
        lbl_directory = QLabel(dj_file.directory)
        layout.addWidget(lbl_filename)
        layout.addWidget(lbl_directory)

        self.btn_open_note = QPushButton('Открыть заметку')
        self.btn_open_note.clicked.connect(self.open_note)
        self.btn_create_note = QPushButton('Создать заметку')
        self.btn_create_note.clicked.connect(self.create_note)
    
        if dj_file.note_path.exists():
            self.btn_open_note.setEnabled(True)
            self.btn_create_note.setEnabled(False)
        else:
            self.btn_open_note.setEnabled(False)
            self.btn_create_note.setEnabled(True)

        layout.addWidget(self.btn_open_note)
        layout.addWidget(self.btn_create_note)

    def open_note(self):
        open_file_with_default_program(f'obsidian://open?file={self.dj_file.note_name}')

    def create_note(self):
        if not self.dj_file.note_path.exists():
            with self.dj_file.note_path.open('w', encoding='utf-8') as note_file:
                note_file.write(f'# {self.dj_file.filename}\n')

            self.btn_open_note.setEnabled(True)
            self.btn_create_note.setEnabled(False)


class GUIAnyFile(GUIEntity):
    dj_model = AnyFile
    actions_class = ActionsAnyFileWidget
    field_order = 'filename'
    fields_search = ['directory', 'filename']
    table_class = FilesList
    window_class = FileWindow