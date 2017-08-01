activate_this = '/home/phenodoop/phenowl/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys, os
import logging
logging.basicConfig(stream=sys.stderr)

sys.path.insert(0,"/home/phenodoop/phenowl/")
sys.path.insert(0,"/home/phenodoop/phenowl/static/")
os.chdir("/home/phenodoop/phenowl")
from restserver import app as application
