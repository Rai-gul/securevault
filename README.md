# SecureVault 🔒

A Django web app for securely storing personal notes and files—notes are encrypted at rest with Fernet.

## Features

- User registration, login, and logout  
- Notes encrypted at rest via `cryptography.fernet`  
- Create, read, update, delete (CRUD) notes  
- Upload and download files per user  
- Search and pagination for notes  
- Unit tests for encryption logic

## Tech Stack

- Python 3.x, Django 4.x  
- cryptography (Fernet)  
- SQLite (default)  
- HTML/CSS with Django templates

## Getting Started

```bash
git clone https://github.com/Rai-gul/securevault.git
cd securevault
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
HEAD


🔒 Security
On each Note.save(), plaintext is encrypted using a Fernet key stored in settings.py.
Templates and forms display plaintext via the note.decrypted_content property.

Quick Example

```bash
python manage.py shell
from filemanager.models import Note
note = Note.objects.create(title="Hello", content="My secret", owner_id=1)
print(note.decrypted_content)  # outputs "My secret"
exit()

Running Tests

```bash
python manage.py test filemanager.tests.test_encryption

Contributing

Fork the repo
Create a new feature branch
Submit a pull request

License

This project is licensed under the MIT License.

```bash
::contentReference[oaicite:0]{index=0}

2df9182 (Publish latest SecureVault with encryption feature)
