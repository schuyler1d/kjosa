"""
WSGI config for kjosa project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
from os.path import normpath, dirname, join as pathjoin
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kjosa.settings")

sys.path[:0] = [normpath(pathjoin(dirname(__file__), x)) for x in ('..', '../vendor/speck/Python')]

application = get_wsgi_application()
