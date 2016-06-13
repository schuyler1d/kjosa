#!/usr/bin/env python
import os
import sys

PROJECT_ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
VENDOR_APP_PATH = os.path.normpath(os.path.join(PROJECT_ROOT_PATH, './vendor/speck/Python'))
sys.path.insert(0, VENDOR_APP_PATH)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kjosa.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
