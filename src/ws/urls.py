from ws.views import scan_view, export_view, import_view, playlist_view

url_patterns = [
    [r'/mediagarden/scan/(?P<type_entity_code>[0-9]+)/', scan_view],
    [r'/mediagarden/export/(?P<type_entity_code>[0-9]+)/', export_view],
    [r'/mediagarden/import/(?P<type_entity_code>[0-9]+)/', import_view],
    [r'/mediagarden/playlist/(?P<type_entity_code>[0-9]+)/', playlist_view],
]
