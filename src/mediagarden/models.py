from django.conf import settings
from django.db import models

from common.models import Tag


MEDIAGROUP_DOCUMENT = 1
MEDIAGROUP_IMAGE = 2
MEDIAGROUP_AUIDO = 3
CHOICES_MEDIAGROUP = (
    (MEDIAGROUP_DOCUMENT, 'Документ'),
    (MEDIAGROUP_IMAGE, 'Картинка'),
    (MEDIAGROUP_AUIDO, 'Аудио'),
)

class AnyFile(models.Model):
    CODE = 1
    hash = models.CharField('Хеш файла', max_length=64, unique=True)
    directory = models.CharField('Директория', max_length=255)
    filename = models.CharField('Имя файла', max_length=255)
    is_deleted = models.BooleanField('Удалён ли', default=False)
    tags = models.ManyToManyField(Tag, related_name='files')
    # TODO: Нужны эти поля?
    mediagroup = models.IntegerField('Тип файла', choices=CHOICES_MEDIAGROUP, default=MEDIAGROUP_DOCUMENT)
    isarchive = models.BooleanField('Флаг архива', default=False)

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

    def update_path(self, inserted_directory, inserted_filename):
        self.directory = inserted_directory
        self.filename = inserted_filename
        self.save()

    class Model:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'


# class BaseMedia(models.Model):
#     file = models.ForeignKey('db.AnyFile', on_delete=models.CASCADE, related_name='%(class)s', null=True)
#     other_fields = models.JSONField('Прочие поля', default=dict)

#     class Meta:
#         abstract = True
#         constraints = [
#             models.UniqueConstraint(fields=['file'], name='%(app_label)s_%(class)s_unique')
#         ]


# class Book(BaseMedia):
#     title = models.CharField('Заголовок', blank=True, default='', max_length=255)
#     isbn = models.CharField('ISBN', blank=True, default='', max_length=13)
#     public_year = models.IntegerField('Год издания', blank=True, default='')

#     class Meta:
#         verbose_name = 'Книга'
#         verbose_name_plural = 'Книги'
