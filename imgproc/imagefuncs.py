import numpy as np
import cv2

class ImageProcessor():
    
    @staticmethod
    def reduce_noise(srcfile, dstfile):
        img = cv2.imread(srcfile)
        result = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        cv2.imwrite(dstfile, result)
    
    @staticmethod
    def convert_color(srcfile, dstfile, code):
        img = cv2.imread(srcfile)
        result = cv2.cvtColor(img, code)
        cv2.imwrite(dstfile, result)
        