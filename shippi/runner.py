import subprocess
import os
from os.path import join, dirname

def run(script, *args):
    this_dir = dirname(os.path.abspath(__file__))
    cmd = join(this_dir, script)
    if args:
        cmd += ' ' + ' '.join(args)
        
    cmd = [r'/usr/bin/python', cmd]
    print(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()

def run_hippi(*args):
    return run('img_pipe2.py', *args)

def run_hippi(*args):
    return run('shippi.py', *args)

