from pathlib import Path

from django.conf import settings
from django.apps import AppConfig
from gardensunion.base.utils import register_gui


class MediaGardenConfig(AppConfig):
    verbose_name = 'МедиаГарден'
    name = 'mediagarden'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings.STORAGE_BOOKS = Path(settings.ENV('STORAGE_BOOKS')).resolve()
        settings.STORAGE_PICTURES = Path(settings.ENV('STORAGE_PICTURES')).resolve()
        settings.STORAGE_AUDIOS = Path(settings.ENV('STORAGE_AUDIOS')).resolve()
        settings.STORAGE_VIDEOS = Path(settings.ENV('STORAGE_VIDEOS')).resolve()
        settings.STORAGE_NOTES = Path(settings.ENV('STORAGE_NOTES')).resolve()

    def ready(self):
        from mediagarden import gui_models
        register_gui(gui_models, 'GUIDocumentFile', 'GUIPictureFile', 'GUIAudioFile', 'GUIVideoFile')
