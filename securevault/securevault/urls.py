from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from filemanager import views as fm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('filemanager.urls')),

    path("files/", fm.file_list, name="file_list"),
    path("notes/", fm.notes_list, name="notes_list"),

    path("files/<uuid:file_id>/delete/", fm.delete_file, name="delete_file"),
    path("notes/<uuid:note_id>/delete/", fm.delete_note, name="delete_note"),
    path("files/<uuid:file_id>/download/", fm.download_file, name="download_file"),

    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)