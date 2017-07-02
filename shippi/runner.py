import subprocess
import os
from os.path import join, dirname
def run(*args):
    this_dir = dirname(os.path.abspath(__file__))
    cmd = join(this_dir, 'img_pipe2.py')
    if args:
        cmd += ' ' + ' '.join(args)
        
    cmd = [r'/usr/bin/python', cmd]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()