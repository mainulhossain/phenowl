from __future__ import print_function
from os import makedirs

__author__ = "Mainul Hossain"
__date__ = "$Dec 10, 2016 2:23:14 PM$"

import os
import sys
import shutil
import tempfile
from urllib.parse import urlparse, urlunparse
from os import listdir
from os.path import isfile, join, isdir

try:
    from hdfs import InsecureClient
except:
    pass

class PosixFileSystem():
    
    def __init__(self):
        self.localdir = path.join(path.abspath(path.dirname(__file__)), 'storage')
    
    def normaize_path(self, path):
        return join(self.localdir, path)
        
    def makedirs(self, path):
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
            
    def addfolder(self, path):
        path = self.normaize_path(path)
        return self.makedirs(path)
    
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
            return reader.read()
        
    def write(self, path, content):
        path = self.normaize_path(path)
        with open(path, 'w') as writer:
            return writer.write(content)
            
class HadoopFileSystem():
    def __init__(self, addr, user):
        self.client = InsecureClient(addr, user=user)
    
    def normaize_path(self, path):
        u = urlparse(path)
        return u.path
        
    def makedirs(self, path):
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
        
    def addfolder(self, path):
        path = self.normaize_path(path)
        return self.makedirs(path)
    
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
            return reader.read()
    
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
    def makedirs(path):
        filesystem = IOHelper.getFileSystem(path)
        filesystem.makedirs(path)
        
    @staticmethod
    def read(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.read(path)
    
    @staticmethod
    def write(path, content):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.write(path, content)
        
if __name__ == "__main__":
    print("Hello World")
