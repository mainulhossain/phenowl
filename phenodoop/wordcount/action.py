import sys
import os
from ..hadoop import run_hadoop

def count_words(input, output):
    cwd = os.path.abspath(os.path.dirname(__file__))
    run_hadoop(os.path.join(cwd, 'mapper.py'), os.path.join(cwd, 'reducer.py'), input, output)