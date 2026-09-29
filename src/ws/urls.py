from ws.views import scan_view, export_view, import_view

url_patterns = [
    [r'/mediagarden/scan/', scan_view],
    [r'/mediagarden/export/', export_view],
    [r'/mediagarden/import/', import_view],
]
