from django.conf import settings
from django.db import models

from gardensunion.base.models import Tag


MEDIAGROUP_DOCUMENT = 1
MEDIAGROUP_IMAGE = 2
MEDIAGROUP_AUIDO = 3
CHOICES_MEDIAGROUP = (
    (MEDIAGROUP_DOCUMENT, 'Документ'),
    (MEDIAGROUP_IMAGE, 'Картинка'),
    (MEDIAGROUP_AUIDO, 'Аудио'),
)

class AnyFile(models.Model):
    CODE = None
    STORAGE = None
    NOTE_PREFIX = None
    STORAGE_NOTES = None

    hash = models.CharField('Хеш файла', max_length=64, unique=True)
    directory = models.CharField('Директория', max_length=255)
    filename = models.CharField('Имя файла', max_length=255)
    is_deleted = models.BooleanField('Удалён ли', default=False)
    # TODO: Нужны эти поля?
    # mediagroup = models.IntegerField('Тип файла', choices=CHOICES_MEDIAGROUP, default=MEDIAGROUP_DOCUMENT)
    isarchive = models.BooleanField('Флаг архива', default=False)

    @property
    def relpath(self):
        return '{}/{}'.format(self.directory, self.filename).removeprefix('/')
    
    @property
    def abspath(self):
        return self.STORAGE / self.directory / self.filename

    @property
    def absdirpath(self):
        return self.STORAGE / self.directory

    @property
    def note_name(self):
        return f'{self.NOTE_PREFIX}_{self.pk}.md'

    @property
    def note_path(self):
        return self.STORAGE_NOTES / self.note_name

    def update_path(self, inserted_directory, inserted_filename):
        self.directory = inserted_directory
        self.filename = inserted_filename
        self.save()

    class Meta:
        abstract = True
        # verbose_name = 'Файл'
        # verbose_name_plural = 'Файлы'


class DocumentFile(AnyFile):
    CODE = 1
    STORAGE = settings.STORAGE_BOOKS
    NOTE_PREFIX = 'книга'
    STORAGE_NOTES = settings.STORAGE_NOTES / 'список_всех_книги'

    tags = models.ManyToManyField(Tag, related_name='documents')

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class PictureFile(AnyFile):
    CODE = 8
    STORAGE = settings.STORAGE_PICTURES
    NOTE_PREFIX = 'изображение'
    STORAGE_NOTES = settings.STORAGE_NOTES / 'список_всех_изображения'

    tags = models.ManyToManyField(Tag, related_name='pictures')

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'


class AudioFile(AnyFile):
    CODE = 9
    STORAGE = settings.STORAGE_AUDIOS
    NOTE_PREFIX = 'аудио'
    STORAGE_NOTES = settings.STORAGE_NOTES / 'список_всех_аудио'

    tags = models.ManyToManyField(Tag, related_name='audios')

    class Meta:
        verbose_name = 'Аудио'
        verbose_name_plural = 'Аудио'


class VideoFile(AnyFile):
    CODE = 10
    STORAGE = settings.STORAGE_VIDEOS
    NOTE_PREFIX = 'видео'
    STORAGE_NOTES = settings.STORAGE_NOTES / 'список_всех_видео'

    tags = models.ManyToManyField(Tag, related_name='videos')

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'


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
#     public_year = models.IntegerField('Год издания', null=True, default=None)

#     class Meta:
#         verbose_name = 'Книга'
#         verbose_name_plural = 'Книги'
