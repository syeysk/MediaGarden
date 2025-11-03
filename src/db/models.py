from django.conf import settings
from django.db import models


class AnyFile(models.Model):
    hash = models.CharField('Хеш файла', max_length=64, unique=True)
    directory = models.CharField('Директория', max_length=255)
    filename = models.CharField('Имя файла', max_length=255)
    is_deleted = models.BooleanField('Удалён ли', default=False)
    
    @property
    def relpath(self):
        return '{}/{}'.format(self.directory, self.filename).removeprefix('/')
    
    @property
    def abspath(self):
        return settings.STORAGE_BOOKS / self.directory / self.filename

    @property
    def absdirpath(self):
        return settings.STORAGE_BOOKS / self.directory

    @property
    def note_name(self):
        return f'книга_{self.pk}.md'

    @property
    def note_path(self):
        return settings.STORAGE_NOTES / self.note_name

    class Model:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'


class Tag(models.Model):
    name = models.CharField('Имя тега', max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True)
    files = models.ManyToManyField(AnyFile, related_name='tags')

    class Model:
        verbose_name = 'Теги'
        verbose_name_plural = 'Тег'
