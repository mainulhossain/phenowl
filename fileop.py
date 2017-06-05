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
    
    def makedirs(self, path):
        if not os.path.exists(path):
            os.makedirs(path) 
        return path
    
    def delete(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
            
    def addfolder(self, path):
        return self.makedirs(path)
    
    def rename(self, oldpath, newpath):
        os.rename(oldpath, newpath)
    
    def get_files(self, path):
        return [f for f in listdir(path) if isfile(join(path, f))]
    
    def get_folders(self, path):
        return [f for f in listdir(path) if isdir(join(path, f))]
    
class HadoopFileSystem():
    def __init__(self, addr, user):
        self.client = InsecureClient(addr, user=user)
    
    def makedirs(self, path):
        try: 
            self.client.makedirs(path)
        except:
            return None
        return path
    
    def delete(self, path):
        try: 
            if self.client.status(path, False) is not None:
                self.client.delete(path, True)
        except Exception as e: print(e)
        
    def addfolder(self, path):
        return self.makedirs(path)
    
    def rename(self, oldpath, newpath):
        try:
            self.client.rename(oldpath, newpath)
        except Exception as e:
            print(e)
    
    def get_files(self, path):
        files = []
        for f in self.client.list(path):
            status = self.client.status(join(path, f), False)
            if status['type'] != "DIRECTORY":
                files.append(f)
        return files
    
    def get_folders(self, path):
        folders = []
        for f in self.client.list(path):
            status = self.client.status(join(path, f), False)
            if status['type'] == "DIRECTORY":
                folders.append(f)
        return folders

class IOHelper():
    @staticmethod
    def getFileSystem(url):
        try:
            u = urlparse(url)
            if u.scheme:
                p = urlunparse((u.scheme, u.netloc, '', '', '', ''))
                return HadoopFileSystem(p, 'hdfs')
        finally:
            return PosixFileSystem()
    
    @staticmethod
    def get_files(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.get_files(path)
    
    @staticmethod
    def get_folders(path):
        filesystem = IOHelper.getFileSystem(path)
        return filesystem.get_folders(path)
 
        
if __name__ == "__main__":
    print("Hello World")
