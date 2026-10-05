import json

from django.conf import settings
from asgiref.sync import sync_to_async
from websockets.asyncio.server import broadcast
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from gardensunion.base.utils import get_dj_model
from mediagarden.scanner import (
    scan_to_db, STATUS_NEW, STATUS_MOVED, STATUS_RENAMED, STATUS_MOVED_AND_RENAMED,
    STATUS_UNTOUCHED, STATUS_DELETED, STATUS_DUPLICATE, export_db, import_csv_to_db
)
from mediagarden.exporters import MarkdownExporter, CSVExporter

ascan_to_db = sync_to_async(scan_to_db)
aexport_db = sync_to_async(export_db)
aimport_csv_to_db = sync_to_async(import_csv_to_db)

type_components = {
    STATUS_NEW: 'new',
    STATUS_MOVED: 'moved',
    STATUS_RENAMED: 'moved',
    STATUS_MOVED_AND_RENAMED: 'moved',
    STATUS_UNTOUCHED: 'untouched',
    STATUS_DELETED: 'deleted',
    STATUS_DUPLICATE: 'dublicated',
}


class Manager:
    def __init__(self, connection):
        self.connection = connection

    def send(self, toes, **body):
        broadcast(toes, json.dumps(body))

    def send_to_me(self, **body):
        self.send([self.connection], **body)


class ManagerScan(Manager):
    def send_card(self, status, inserted_anyfile, existed_anyfile):
        if status != STATUS_UNTOUCHED:
            self.send_to_me(
                type='card',
                status=type_components[status],
                inserted_path=str(inserted_anyfile.relpath) if inserted_anyfile else None,
                existed_path=str(existed_anyfile.relpath) if existed_anyfile else None,
                inserted_id=inserted_anyfile.id if inserted_anyfile else None,
                existed_id=existed_anyfile.id if existed_anyfile else None,
            )
            if status in {STATUS_MOVED, STATUS_RENAMED, STATUS_MOVED_AND_RENAMED}:
                existed_anyfile.update_path(inserted_anyfile.directory, inserted_anyfile.filename)

    def count_scanned_files(self, count):
        self.send_to_me(type='count', count_scanned_files=count)

    def progress_current_file(self, filepath):
        self.send_to_me(type='filepath', progress_current_file=filepath)


class ManagerExport(Manager):
    def progress(self, index_of_current_row, count_rows, csv_current_page):
        self.send_to_me(type='count', index_row=index_of_current_row, count_rows=count_rows, index_page=csv_current_page)


class ManagerImport(Manager):
    def progress(self, index_of_current_row):
        self.send_to_me(type='count', index_row=index_of_current_row)


async def scan_view(conection, type_entity_code):
    gui_model = get_dj_model(int(type_entity_code))
    manager = ManagerScan(conection)
    while True:
        try:
            data_str = await conection.recv()
            if data_str:
                data_json = json.loads(data_str)
                command = data_json.get('command')
                if command == 'start':
                    await ascan_to_db(
                        gui_model.dj_model,
                        manager.count_scanned_files,
                        manager.progress_current_file,
                        manager.send_card,
                    )
        except ConnectionClosedOK as _:
            break
        except ConnectionClosedError as _:
            break
        except Exception as error:
            raise error


async def export_view(conection, type_entity_code):
    gui_model = get_dj_model(int(type_entity_code))
    manager = ManagerExport(conection)
    while True:
        try:
            data_str = await conection.recv()
            if data_str:
                data_json = json.loads(data_str)
                command = data_json.get('command')
                format = data_json.get('format')
                if command == 'export':
                    exporter_class = None
                    if format == 'markdown':
                        exporter_class = MarkdownExporter
                    elif format == 'csv':
                        exporter_class = CSVExporter

                    await aexport_db(gui_model.dj_model, exporter_class, manager.progress)
        except ConnectionClosedOK as _:
            break
        except ConnectionClosedError as _:
            break
        except Exception as error:
            raise error



async def import_view(conection, type_entity_code):
    gui_model = get_dj_model(int(type_entity_code))
    manager = ManagerImport(conection)
    while True:
        try:
            data_str = await conection.recv()
            if data_str:
                data_json = json.loads(data_str)
                command = data_json.get('command')
                if command == 'import':
                    await aimport_csv_to_db(gui_model.dj_model, manager.progress)
        except ConnectionClosedOK as _:
            break
        except ConnectionClosedError as _:
            break
        except Exception as error:
            raise error
