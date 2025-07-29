from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .forms import FileUploadForm, NoteForm, CustomUserCreationForm
from django.contrib.auth.models import User
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
from .forms import FileUploadForm, NoteForm
from django.contrib.auth import logout
from django.shortcuts import redirect

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
        model = User
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
        total_size = sum(f.size for f in UploadedFile.objects.filter(owner=request.user))
        
        def format_file_size(size):
            """Helper function to format file size"""
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
            email = form.cleaned_data.get('email')
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
    
    # Sorting
    if sort_by == 'name':
        files = files.order_by('name')
    elif sort_by == 'size':
        files = files.order_by('-size')
    else:  # default to date
        files = files.order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(files, 12)  # 12 files per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'filemanager/file_list.html', context)

@login_required
def upload_file(request):
    """Handle file uploads"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.owner = request.user
            
            # Set mime type
            file_obj = request.FILES['file']
            mime_type, _ = mimetypes.guess_type(file_obj.name)
            uploaded_file.mime_type = mime_type or 'application/octet-stream'
            
            # Determine file type
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
                # AJAX request
                return JsonResponse({
                    'success': True,
                    'message': f'File "{uploaded_file.name}" uploaded successfully!',
                    'file_id': str(uploaded_file.id)
                })
            else:
                messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
                return redirect('file_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Upload failed. Please check your file and try again.'
                })
    else:
        form = FileUploadForm()
    
    return render(request, 'filemanager/upload.html', {'form': form})

@login_required
def download_file(request, file_id):
    """Handle file downloads"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, owner=request.user)
    
    # Increment download count
    file_obj.download_count += 1
    file_obj.save()
    
    # Serve file
    if os.path.exists(file_obj.file.path):
        with open(file_obj.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=file_obj.mime_type)
            response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
            return response
    else:
        raise Http404("File not found")

@login_required
def delete_file(request, file_id):
    """Delete a file"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, owner=request.user)
    
    if request.method == 'POST':
        # Delete physical file
        if os.path.exists(file_obj.file.path):
            os.remove(file_obj.file.path)
        
        file_name = file_obj.name
        file_obj.delete()
        
        messages.success(request, f'File "{file_name}" deleted successfully!')
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
    
    # Pagination
    paginator = Paginator(notes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'filemanager/notes_list.html', context)

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
    
    return render(request, 'filemanager/note_form.html', {'form': form, 'note': note})

@login_required
def delete_note(request, note_id):
    """Delete a note"""
    note = get_object_or_404(Note, id=note_id, owner=request.user)
    
    if request.method == 'POST':
        note_title = note.title
        note.delete()
        messages.success(request, f'Note "{note_title}" deleted successfully!')
        return redirect('notes_list')
    
    return render(request, 'filemanager/confirm_delete_note.html', {'note': note})

# API endpoints for AJAX requests
@login_required
@csrf_exempt
def api_upload_file(request):
    """API endpoint for file uploads via AJAX"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            file_obj = request.FILES['file']
            
            # Check file size (50MB limit)
            if file_obj.size > 50 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'message': 'File too large. Maximum size is 50MB.'
                })
            
            # Create UploadedFile instance
            uploaded_file = UploadedFile(
                file=file_obj,
                owner=request.user,
                description=request.POST.get('description', '')
            )
            
            # Set mime type and file type
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
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.file_size_formatted
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Upload failed: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

@login_required
def bulk_delete_files(request):
    """Delete multiple files"""
    if request.method == 'POST':
        file_ids = request.POST.getlist('file_ids')
        deleted_count = 0
        
        for file_id in file_ids:
            try:
                file_obj = UploadedFile.objects.get(id=file_id, owner=request.user)
                # Delete physical file
                if os.path.exists(file_obj.file.path):
                    os.remove(file_obj.file.path)
                file_obj.delete()
                deleted_count += 1
            except UploadedFile.DoesNotExist:
                continue
        
        messages.success(request, f'{deleted_count} files deleted successfully!')
        return redirect('file_list')
    
    return redirect('file_list')

@login_required
def file_preview(request, file_id):
    """API endpoint for file preview"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, owner=request.user)
    
    if file_obj.file_type == 'image':
        return JsonResponse({
            'success': True,
            'type': 'image',
            'url': file_obj.file.url,
            'name': file_obj.name
        })
    elif file_obj.file_type in ['video', 'audio']:
        return JsonResponse({
            'success': True,
            'type': file_obj.file_type,
            'url': file_obj.file.url,
            'name': file_obj.name
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Preview not available for this file type'
        })