from mediagarden.models import DocumentFile, PictureFile, AudioFile, VideoFile


class GUIDocumentFile:
    dj_model = DocumentFile
    window_name = 'any_file'
    window_fields = ['filename', 'directory', 'hash']
    table_fields = ['filename', 'directory']
    table_name = 'any_file'
    field_order = 'filename'
    fields_search = ['directory', 'filename']
    actions = {
        'scan': 'Сканирование',
        'export': 'Экспорт в заметки',
        'import': 'Импорт из заметок',
    }

    def populate_extra_window_fields(entity: DocumentFile, fields: dict):
        fields['note_uri'] = {'value': f'obsidian://open?file={entity.note_name}'}
        fields['note_exists'] = {'value': entity.note_path.exists()}


class GUIPictureFile():
    dj_model = PictureFile
    window_name = 'any_file'
    window_fields = ['filename', 'directory', 'hash']
    table_fields = ['filename', 'directory']
    table_name = 'any_file'
    field_order = 'filename'
    fields_search = ['directory', 'filename']
    actions = {
        'scan': 'Сканирование',
        'export': 'Экспорт в заметки',
        'import': 'Импорт из заметок',
    }

    def populate_extra_window_fields(entity: PictureFile, fields: dict):
        fields['note_uri'] = {'value': f'obsidian://open?file={entity.note_name}'}
        fields['note_exists'] = {'value': entity.note_path.exists()}


class GUIAudioFile():
    dj_model = AudioFile
    window_name = 'any_file'
    window_fields = ['filename', 'directory', 'hash']
    table_fields = ['filename', 'directory']
    table_name = 'any_file'
    field_order = 'filename'
    fields_search = ['directory', 'filename']
    actions = {
        'scan': 'Сканирование',
        'export': 'Экспорт в заметки',
        'import': 'Импорт из заметок',
        'playlist': 'Сохранить как плейлист',
    }

    def populate_extra_window_fields(entity: AudioFile, fields: dict):
        fields['note_uri'] = {'value': f'obsidian://open?file={entity.note_name}'}
        fields['note_exists'] = {'value': entity.note_path.exists()}


class GUIVideoFile():
    dj_model = VideoFile
    window_name = 'any_file'
    window_fields = ['filename', 'directory', 'hash']
    table_fields = ['filename', 'directory']
    table_name = 'any_file'
    field_order = 'filename'
    fields_search = ['directory', 'filename']
    actions = {
        'scan': 'Сканирование',
        'export': 'Экспорт в заметки',
        'import': 'Импорт из заметок',
    }

    def populate_extra_window_fields(entity: VideoFile, fields: dict):
        fields['note_uri'] = {'value': f'obsidian://open?file={entity.note_name}'}
        fields['note_exists'] = {'value': entity.note_path.exists()}
