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
        future = self.pool.submit(func, *args)
        self.futures.append(future)
        return future.result()
    
    def submit(self, argv):
        self.cleanup_pool()
        execfile = argv[:1]
        args = argv[1:]
        future = self.pool.submit(check_output, ' '.join(argv), shell=True)
        self.futures.append(future)
        return future.result()
        
    def cleanup_pool(self):
        self.futures = list(filter(lambda f : f and not f.done(), self.futures))
                
task_manager = TaskManager()
