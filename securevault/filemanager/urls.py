from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    
    # File management
    path('files/', views.file_list, name='file_list'),
    path('upload/', views.upload_file, name='upload_file'),
    path('download/<uuid:file_id>/', views.download_file, name='download_file'),
    path('delete/<uuid:file_id>/', views.delete_file, name='delete_file'),
    path('bulk-delete/', views.bulk_delete_files, name='bulk_delete_files'),
    path('preview/<uuid:file_id>/', views.file_preview, name='file_preview'),
    
    # Notes management
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/create/', views.create_note, name='create_note'),
    path('notes/edit/<uuid:note_id>/', views.edit_note, name='edit_note'),
    path('notes/delete/<uuid:note_id>/', views.delete_note, name='delete_note'),
    
    # API endpoints
    path('api/upload/', views.api_upload_file, name='api_upload_file'),
    path('logout/', views.custom_logout, name='logout'),
]
