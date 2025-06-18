import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, PROJECT_DIR)

VENV_DIR = os.path.join(PROJECT_DIR, 'venv')

site_packages_path = os.path.join(VENV_DIR, 'lib', 'python3.8', 'site-packages')
sys.path.insert(0, site_packages_path)

from app import app as application
