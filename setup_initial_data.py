import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','tycoons_lounge.settings')
import django; django.setup()
from django.contrib.auth.models import User
username = 'admin'
password = 'admin123'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, 'admin@example.com', password)
    print('Created admin/admin123')
else:
    print('Admin already exists')
