from django.urls import path
from mediagarden.views import (
    DocumentNoteView,
    DocumentOpenView,
    ActionScanView,
    PictureView,
)

urlpatterns = [
    path('type/<int:type_entity_code>/any_file/<int:any_file_id>/note/', DocumentNoteView.as_view(), name='note'),
    path('type/<int:type_entity_code>/any_file/<int:any_file_id>/open/', DocumentOpenView.as_view(), name='open'),    
    path('type/<int:type_entity_code>/action/scan/', ActionScanView.as_view(), name='open'),    
    path('type/<int:type_entity_code>/picture/<int:any_file_id>/', PictureView.as_view(), name='picture'),        
]