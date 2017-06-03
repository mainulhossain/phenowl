from __future__ import print_function

from concurrent.futures import ThreadPoolExecutor
from subprocess import call, check_output
from past.builtins.misc import execfile
import sys

class TaskManager:
    def __init__(self, max_count = 5):
        self.pool = ThreadPoolExecutor(max_count)
        self.futures = []
        
    def submit_func(self, func, *args):
        self.cleanup_pool()
        self.futures.append(self.pool.submit(func, *args))
    
    def submit(self, argv):
        self.cleanup_pool()
        execfile = argv[:1]
        args = argv[1:]
        self.futures.append(self.pool.submit(check_output, ' '.join(argv), shell=True))
        
    def cleanup_pool(self):
        list(filter(lambda f : f and not f.done(), self.futures))
                
task_manager = TaskManager()
