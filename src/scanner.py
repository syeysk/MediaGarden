import csv
import hashlib

STATUS_NEW = 'Новый'
STATUS_MOVED = 'Переместили'
STATUS_RENAMED = 'Переименовали'
STATUS_MOVED_AND_RENAMED = 'Переместили и переименовали'
STATUS_UNTOUCHED = 'Не тронут'
STATUS_DELETED = 'Удалён'
STATUS_DUPLICATE = 'Дубликат'
LIBRARY_IGNORE_EXTENSIONS = ['db', 'db-journal']


import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings') 
django.setup()

from django.conf import settings
from django.db.models import Q, Count
from db.models import AnyFile, Tag


def get_file_hash(file_path):
    BLOCKSIZE = 65536
    hasher = hashlib.blake2s()
    with open(file_path, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)

    return hasher.hexdigest()


class DBStorage:
    COUNT_ROWS_FOR_INSERT = 30
    COUNT_ROWS_ON_PAGE = 30

    def insert_tag(self, name, parent_id=None):
        tag = Tag(name=name, parent_id=parent_id)
        tag.save()
        return tag

    def select_tags(self, parent_id=None):
        return Tag.objects.filter(parent_id=parent_id)

    def get_count_pages(self, total_rows_count) -> int:
        count_pages = total_rows_count // self.COUNT_ROWS_ON_PAGE
        return count_pages + 1 if total_rows_count % self.COUNT_ROWS_ON_PAGE > 0 else count_pages
    
    def _build_queryset(self, tags=None, search=''):
        queryset = AnyFile.objects
        if search:
            queryset = queryset.filter(Q(directory__contains=search) | Q(filename__contains=search))
        
        if tags:
            queryset = queryset.filter(tags__pk__in=tags).annotate(Count('pk'))

        return queryset

    def select_count(self, tags=None, search=''):
        return self._build_queryset(tags, search).count()

    def select_rows(self, tags=None, search=''):
        queryset = self._build_queryset(tags, search).order_by('filename')
        count_pages = self.get_count_pages(queryset.count())
        for page_num in range(count_pages):
            offset = page_num * self.COUNT_ROWS_ON_PAGE
            for anyfile in queryset[offset:offset + self.COUNT_ROWS_ON_PAGE]:
                yield anyfile

    def insert_file(self, file_hash, file_id, inserted_file):
        AnyFile(hash=file_hash, pk=file_id, directory=os.path.dirname(inserted_file), filename=os.path.basename(inserted_file))


class LibraryStorage:
    CSV_COUNT_ROWS_ON_PAGE = 100

    def __init__(self) -> None:
        """Инициализирует класс сканера хранилища"""
        self.db = DBStorage()

    def scan_to_db(
            self,
            progress_count_scanned_files=None,
            progress_current_file=None,
            func=None,
    ):
        """Сканирует информацию о файлах в директории и заносит её в базу"""
        AnyFile.objects.update(is_deleted=True)
        os.chdir(settings.STORAGE_BOOKS)
        total_count_files = 0
        for directory, _, filenames in os.walk('./'):
            directory = directory[2:]
            if os.path.sep == '\\':
                directory = directory.replace('\\', '/')

            for filename in filenames:
                if filename.split('.')[-1] in LIBRARY_IGNORE_EXTENSIONS:
                    continue  # останется отмеченным как удалённый, а потому в структуру (экспорт) не попадёт

                full_path = os.path.join(directory, filename)
                if progress_current_file:
                    progress_current_file(full_path)

                file_hash = get_file_hash(full_path)
                total_count_files += 1
                if progress_count_scanned_files:
                    progress_count_scanned_files(total_count_files)

                inserted_anyfile = AnyFile(hash=file_hash, directory=directory, filename=filename)
                existed_anyfile = AnyFile.objects.filter(hash=file_hash).first()
                if existed_anyfile:
                    existed_anyfile.is_deleted = False
                    existed_anyfile.save()
                else:
                    inserted_anyfile.save()

                status = self.get_file_status(inserted_anyfile, existed_anyfile)
                if func:
                    func(status, inserted_anyfile, existed_anyfile)

        for existed_anyfile in AnyFile.objects.filter(is_deleted=True):
            if func:
                func(STATUS_DELETED, None, existed_anyfile)

    def export_db(self, exporter_class, progress_count_exported_files=None) -> None:
        """
        Экспортирует из базы следующую информацию о файле:
        хэш,идентификатор,директория,имя файла
        """
        csv_current_page = 1
        exporter = exporter_class(settings.STORAGE_NOTES, settings.STORAGE_BOOKS)
        exporter.open_new_page(csv_current_page)
        number_of_last_row_on_current_page = self.CSV_COUNT_ROWS_ON_PAGE
        count_rows = AnyFile.objects.count()
        index_of_current_row = None
        for index_of_current_row, anyfile in enumerate(AnyFile.objects.order_by('id')):
            number_of_last_row_on_current_page = number_of_last_row_on_current_page - anyfile.pk + 1
            if index_of_current_row >= number_of_last_row_on_current_page:
                exporter.close(is_last_page=index_of_current_row == count_rows - 1)
                number_of_last_row_on_current_page += self.CSV_COUNT_ROWS_ON_PAGE
                csv_current_page += 1
                exporter.open_new_page(csv_current_page)
                if progress_count_exported_files:
                    progress_count_exported_files(index_of_current_row + 1, count_rows, csv_current_page)

            exporter.write_row((anyfile.hash, anyfile.id, anyfile.directory, anyfile.filename))
            number_of_last_row_on_current_page += anyfile.pk

        if progress_count_exported_files and index_of_current_row is not None:
            progress_count_exported_files(index_of_current_row + 1, count_rows, csv_current_page)

        exporter.close(is_last_page=index_of_current_row is None or index_of_current_row == count_rows - 1)

        with open(os.path.join(exporter.storage_structure, 'tags.csv'), 'w', encoding='utf-8', newline='\n') as csv_file:
            csv_writer = csv.writer(csv_file)
            for row in Tag.objects.values_list('pk', 'name', 'parent_id'):
                csv_writer.writerow(row)

        with open(os.path.join(exporter.storage_structure, 'tags-files.csv'), 'w', encoding='utf-8', newline='\n') as csv_file:
            csv_writer = csv.writer(csv_file)
            for tag in Tag.objects.all():
                for row in tag.files.values_list('pk'):
                    csv_writer.writerow((row[0], tag.pk))

    def import_csv_to_db(self, progress_count_imported_files):
        index_of_current_row = 0
        for csv_filename in os.scandir(settings.STORAGE_NOTES):
            if csv_filename.name in ('tags.csv', 'tags-files.csv'):
                continue

            with open(csv_filename.path, 'r', encoding='utf-8', newline='\n') as csv_file:
                for csv_row in csv.reader(csv_file):
                    anyfile = AnyFile.objects.create(pk=csv_row[1], hash=csv_row[0], directory=csv_row[2], filename=csv_row[3])
                    progress_count_imported_files(index_of_current_row := index_of_current_row + 1)

        with open(settings.STORAGE_NOTES / 'tags.csv', 'r', encoding='utf-8', newline='\n') as csv_file:
            for csv_row in csv.reader(csv_file):
                Tag.objects.create(pk=csv_row[0], name=csv_row[1], parent_id=csv_row[2])

        with open(settings.STORAGE_NOTES / 'tags-files.csv', 'r', encoding='utf-8', newline='\n') as csv_file:
            for csv_row in csv.reader(csv_file):
                anyfile = AnyFile.objects.filter(pk=csv_row[0]).first()
                tag = Tag.objects.filter(pk=csv_row[1]).first()
                tag.files.add(anyfile)

    def get_file_status(self, inserted_anyfile, existed_anyfile):
        if existed_anyfile is None:
            return STATUS_NEW

        is_replaced = inserted_anyfile.directory != existed_anyfile.directory
        is_renamed = inserted_anyfile.filename != existed_anyfile.filename
        is_exists = os.path.exists(existed_anyfile.relpath)
        if is_replaced and not is_renamed:
            return STATUS_DUPLICATE if is_exists else STATUS_MOVED
        elif not is_replaced and is_renamed:
            return STATUS_DUPLICATE if is_exists else STATUS_RENAMED
        elif is_replaced and is_renamed:
            return STATUS_DUPLICATE if is_exists else STATUS_MOVED_AND_RENAMED

        return STATUS_UNTOUCHED
