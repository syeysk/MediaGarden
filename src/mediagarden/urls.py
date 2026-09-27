from django.urls import path
from mediagarden.views import (
    NoteView,
    OpenView,
)

urlpatterns = [
    path('any_file/<int:any_file_id>/note/', NoteView.as_view(), name='note'),
    path('any_file/<int:any_file_id>/open/', OpenView.as_view(), name='open'),    
]