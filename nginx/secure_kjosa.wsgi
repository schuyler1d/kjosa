#! /usr/bin/env python

import os
from os.path import normpath, dirname, join as pathjoin
import sys
# to avoid deadlock.  See: http://code.google.com/p/modwsgi/wiki/ApplicationIssues#Non_Blocking_Module_Imports 
import _strptime

sys.stdout=sys.stderr

import site
site.addsitedir('/usr/local/virtualenvs/django/lib/python3.%d/site-packages' % sys.version_info[1])

sys.path[:0] = [normpath(pathjoin(dirname(__file__), x)) for x in ('..', )]

os.environ['DJANGO_SETTINGS_MODULE'] = 'kjosa.settings'
os.environ['PYTHON_EGG_CACHE']='/tmp/kjosa.ggs'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
