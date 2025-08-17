# securevault/urls.py (or app urls included there)
from django.urls import path
from filemanager import views as fm

urlpatterns = [
    path("", fm.home, name="home"),
    path("files/", fm.file_list, name="file_list"),
    path("files/upload/", fm.upload_file, name="upload_file"),
    path("files/<uuid:file_id>/download/", fm.download_file, name="download_file"),
    path("files/<uuid:file_id>/delete/", fm.delete_file, name="delete_file"),
    path("files/bulk-delete/", fm.bulk_delete_files, name="bulk_delete_files"),
    path("files/<uuid:file_id>/preview/", fm.file_preview, name="file_preview"),

    path("notes/", fm.notes_list, name="notes_list"),
    path("notes/create/", fm.create_note, name="create_note"),
    path("notes/<uuid:note_id>/edit/", fm.edit_note, name="edit_note"),
    path("notes/<uuid:note_id>/delete/", fm.delete_note, name="delete_note"),

    path("register/", fm.register, name="register"),
    path("logout/", fm.custom_logout, name="logout"),
]
