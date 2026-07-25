import os
import sys
import django
from django.conf import settings

# 1. Add package root to sys.path
sys.path.insert(0, os.path.abspath('..'))

# 2. Minimal Django setup so autodoc can load your package code
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django_accounting', # Your package name
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
    )
    django.setup()

# 3. Project Information
project = 'django_accounting'
copyright = '2026, Your Name'
author = 'Your Name'

# 4. Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',  # Enables Google & NumPy style docstrings
]

html_theme = 'sphinx_rtd_theme'
