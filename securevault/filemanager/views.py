from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django import forms
import mimetypes
import os
import json

from .models import UploadedFile, Note
from .forms import FileUploadForm, NoteForm, CustomUserCreationForm


# Custom registration form with email
class CustomUserCreationForm(CustomUserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    class Meta:
        model = CustomUserCreationForm.Meta.model
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a unique username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


def custom_logout(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, "You've been logged out successfully!")
    return redirect('home')


def home(request):
    """Main dashboard view"""
    if request.user.is_authenticated:
        # Get user's recent files and notes
        recent_files = UploadedFile.objects.filter(owner=request.user)[:5]
        recent_notes = Note.objects.filter(owner=request.user)[:5]

        # Get statistics
        total_files = UploadedFile.objects.filter(owner=request.user).count()
        total_size = sum(f.size for f in recent_files)

        def format_file_size(size):
            if size == 0:
                return "0 B"
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"

        context = {
            'recent_files': recent_files,
            'recent_notes': recent_notes,
            'total_files': total_files,
            'total_size': format_file_size(total_size),
        }
        return render(request, 'filemanager/dashboard.html', context)
    else:
        return render(request, 'filemanager/landing.html')


def register(request):
    """User registration with email"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Welcome to SecureVault.')
            # Auto-login after registration
            user = authenticate(username=user.username, password=form.cleaned_data['password1'])
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def file_list(request):
    """Display all user files with search and pagination"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'date')

    files = UploadedFile.objects.filter(owner=request.user)

    if search_query:
        files = files.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if sort_by == 'name':
        files = files.order_by('name')
    elif sort_by == 'size':
        files = files.order_by('-size')
    else:
        files = files.order_by('-uploaded_at')

    paginator = Paginator(files, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'filemanager/file_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    })


@login_required
def upload_file(request):
    """Handle file uploads"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.owner = request.user

            file_obj = request.FILES['file']
            mime_type, _ = mimetypes.guess_type(file_obj.name)
            uploaded_file.mime_type = mime_type or 'application/octet-stream'

            if mime_type:
                if mime_type.startswith('image/'):
                    uploaded_file.file_type = 'image'
                elif mime_type.startswith('video/'):
                    uploaded_file.file_type = 'video'
                elif mime_type.startswith('audio/'):
                    uploaded_file.file_type = 'audio'
                elif mime_type in ['application/zip', 'application/x-rar', 'application/x-7z-compressed']:
                    uploaded_file.file_type = 'archive'
                elif mime_type in ['application/pdf', 'application/msword', 'text/plain']:
                    uploaded_file.file_type = 'document'

            uploaded_file.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'File "{uploaded_file.name}" uploaded successfully!',
                    'file_id': str(uploaded_file.id)
                })
            else:
                messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
                return redirect('file_list')
    else:
        form = FileUploadForm()

    return render(request, 'filemanager/upload.html', {'form': form})


@login_required
def download_file(request, file_id):
    """Handle file downloads"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, owner=request.user)
    file_obj.download_count += 1
    file_obj.save()

    if os.path.exists(file_obj.file.path):
        with open(file_obj.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=file_obj.mime_type)
            response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
            return response
    else:
        raise Http404("File not found")


@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id, owner=request.user)
    if request.method == 'POST':
        if os.path.exists(file_obj.file.path):
            os.remove(file_obj.file.path)
        file_obj.delete()
        messages.success(request, f'File "{file_obj.name}" deleted successfully!')
        return redirect('file_list')
    return render(request, 'filemanager/confirm_delete.html', {'file': file_obj})


@login_required
def notes_list(request):
    """Display all user notes"""
    search_query = request.GET.get('search', '')
    notes = Note.objects.filter(owner=request.user)

    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    paginator = Paginator(notes, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'filemanager/notes_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


@login_required
def create_note(request):
    """Create a new note"""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            messages.success(request, f'Note "{note.title}" created successfully!')
            return redirect('notes_list')
    else:
        form = NoteForm()

    return render(request, 'filemanager/note_form.html', {'form': form})


@login_required
def edit_note(request, note_id):
    """Edit an existing note"""
    note = get_object_or_404(Note, id=note_id, owner=request.user)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f'Note "{note.title}" updated successfully!')
            return redirect('notes_list')
    else:
        form = NoteForm(instance=note)
        # Load decrypted content into the form
        form.fields['content'].initial = note.decrypted_content

    return render(request, 'filemanager/note_form.html', {
        'form': form,
        'note': note
    })


@login_required
def delete_note(request, note_id):
    """Delete a note"""
    note = get_object_or_404(Note, id=note_id, owner=request.user)
    if request.method == 'POST':
        title = note.title
        note.delete()
        messages.success(request, f'Note "{title}" deleted successfully!')
        return redirect('notes_list')
    return render(request, 'filemanager/confirm_delete_note.html', {'note': note})


@login_required
@csrf_exempt
def api_upload_file(request):
    """API endpoint for file uploads via AJAX"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            file_obj = request.FILES['file']
            if file_obj.size > 50 * 1024 * 1024:
                return JsonResponse({'success': False, 'message': 'File too large. Maximum size is 50MB.'})
            uploaded_file = UploadedFile(
                file=file_obj,
                owner=request.user,
                description=request.POST.get('description', '')
            )
            mime_type, _ = mimetypes.guess_type(file_obj.name)
            uploaded_file.mime_type = mime_type or 'application/octet-stream'
            if mime_type:
                if mime_type.startswith('image/'):
                    uploaded_file.file_type = 'image'
                elif mime_type.startswith('video/'):
                    uploaded_file.file_type = 'video'
                elif mime_type.startswith('audio/'):
                    uploaded_file.file_type = 'audio'
                elif mime_type in ['application/zip', 'application/x-rar']:
                    uploaded_file.file_type = 'archive'
                elif mime_type in ['application/pdf', 'application/msword', 'text/plain']:
                    uploaded_file.file_type = 'document'
            uploaded_file.save()
            return JsonResponse({
                'success': True,
                'message': f'File "{uploaded_file.name}" uploaded successfully!',
                'file_id': str(uploaded_file.id),
                'file_name': uploaded_file.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Upload failed: {e}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def bulk_delete_files(request):
    """Delete multiple files"""
    if request.method == 'POST':
        ids = request.POST.getlist('file_ids')
        count = 0
        for fid in ids:
            try:
                f = UploadedFile.objects.get(id=fid, owner=request.user)
                if os.path.exists(f.file.path):
                    os.remove(f.file.path)
                f.delete()
                count += 1
            except UploadedFile.DoesNotExist:
                continue
        messages.success(request, f'{count} files deleted successfully!')
        return redirect('file_list')
    return redirect('file_list')


@login_required
def file_preview(request, file_id):
    """API endpoint for file preview"""
    f = get_object_or_404(UploadedFile, id=file_id, owner=request.user)
    if f.file_type == 'image':
        return JsonResponse({'success': True, 'type': 'image', 'url': f.file.url, 'name': f.name})
    elif f.file_type in ['video', 'audio']:
        return JsonResponse({'success': True, 'type': f.file_type, 'url': f.file.url, 'name': f.name})
    return JsonResponse({'success': False, 'message': 'Preview not available for this file type'})
