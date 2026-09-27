from mediagarden.models import AnyFile


class GUIAnyFile:
    dj_model = AnyFile
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

    def populate_extra_window_fields(entity: AnyFile, fields: dict):
        fields['note_uri'] = {'value': f'obsidian://open?file={entity.note_name}'}
        fields['note_exists'] = {'value': entity.note_path.exists()}
