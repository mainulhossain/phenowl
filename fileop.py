from __future__ import print_function

from os import listdir
from os import makedirs
import os
from os.path import isfile, join, isdir, abspath, dirname
import shutil
import sys
import tempfile
from urllib.parse import urlparse, urlunparse


__author__ = "Mainul Hossain"
__date__ = "$Dec 10, 2016 2:23:14 PM$"


try:
    from hdfs import InsecureClient
except:
    pass

class PosixFileSystem():
    
    def __init__(self):
        self.localdir = join(abspath(dirname(__file__)), 'storage')
    
    def normaize_path(self, path):
        path = os.path.normpath(path)
        if path and path[0] == os.sep:
             path = path[1:]
        return join(self.localdir, path)
        
    def create_folder(self, path):
        path = self.normaize_path(path)
        if not os.path.exists(path):
            os.makedirs(path) 
        return path
    
    def remove(self, path):
        path = self.normaize_path(path)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
               
    def rename(self, oldpath, newpath):
        path = self.normaize_path(path)
        os.rename(oldpath, newpath)
    
    def get_files(self, path):
        path = self.normaize_path(path)
        return [f for f in listdir(path) if isfile(join(path, f))]
    
    def get_folders(self, path):
        path = self.normaize_path(path)
        return [f for f in listdir(path) if isdir(join(path, f))]
    
    def read(self, path):
        path = self.normaize_path(path)
        with open(path) as reader:
            return reader.read().decode('utf-8')
        
    def write(self, path, content):
        path = self.normaize_path(path)
        with open(path, 'w') as writer:
            return writer.write(content)
        
    def unique_filename(self, path, prefix, ext):
        make_fn = lambda i: os.path.join(path, '{0}({1}).{2}'.format(prefix, i, ext))

        for i in range(1, sys.maxsize):
            uni_fn = make_fn(i)
            if not os.path.exists(uni_fn):
                return uni_fn
    
    def isfile(self, path):
        return os.path.isfile(path)
                       
class HadoopFileSystem():
    def __init__(self, addr, user):
        self.client = InsecureClient(addr, user=user)
    
    def normaize_path(self, path):
        u = urlparse(path)
        return u.path
        
    def create_folder(self, path):
        try:
            path = self.normaize_path(path)
            self.client.makedirs(path)
        except:
            return None
        return path
    
    def remove(self, path):
        try: 
            path = self.normaize_path(path)
            if self.client.status(path, False) is not None:
                self.client.delete(path, True)
        except Exception as e: print(e)
           
    def rename(self, oldpath, newpath):
        try:
            oldpath = self.normaize_path(oldpath)
            newpath = self.normaize_path(newpath)
            self.client.rename(oldpath, newpath)
        except Exception as e:
            print(e)
    
    def get_files(self, path):
        path = self.normaize_path(path)
        files = []
        for f in self.client.list(path):
            status = self.client.status(join(path, f), False)
            if status['type'] != "DIRECTORY":
                files.append(f)
        return files
    
    def isfile(self, path):
        filename = os.path.basename(path) 
        files = self.get_files(os.path.dirname(path))
        for file in files:
            if file == filename:
                return True
        return False
    
    def get_folders(self, path):
        path = self.normaize_path(path)
        folders = []
        for f in self.client.list(path):
            status = self.client.status(join(path, f), False)
            if status['type'] == "DIRECTORY":
                folders.append(f)
        return folders
    
    def read(self, path):
        path = self.normaize_path(path)
        with self.client.read(path) as reader:
            return reader.read().decode('utf-8')
    
    def write(self, path, content):
        path = self.normaize_path(path)
        self.client.write(path, content)
            
class IOHelper():
    @staticmethod
    def getFileSystem(url):
        try:
            u = urlparse(url)
            if u.scheme:
                p = urlunparse((u.scheme, u.netloc, '', '', '', ''))
                return HadoopFileSystem(p, 'hdfs')
        except:
            pass
        return PosixFileSystem()
    
    @staticmethod
    def get_files(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.get_files(path)
    
    @staticmethod
    def get_folders(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.get_folders(path)
    
    @staticmethod
    def remove(path):
        filesystem = IOHelper.getFileSystem(path)
        filesystem.remove(path)
        
    @staticmethod
    def create_folder(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.create_folder(path)
        
    @staticmethod
    def read(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.read(path)
    
    @staticmethod
    def normaize_path(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.normaize_path(path)
    
    @staticmethod
    def write(path, content):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.write(path, content)
    
    @staticmethod
    def unique_filename(path, prefix, ext):
        filesystem = IOHelper.getFileSystem(path)
        
        make_fn = lambda i: os.path.join(path, '{0}({1}).{2}'.format(prefix, i, ext))

        for i in range(1, sys.maxsize):
            uni_fn = make_fn(i)
            if not filesystem.isfile(uni_fn):
                return uni_fn
                
if __name__ == "__main__":
    print("Hello World")
