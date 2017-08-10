
#@author: Amit Kumar Mondal
#@address: SR LAB, Computer Science Department, USASK
#Email: amit.mondal@usask.ca
import paramiko
import re
import sys
import os
import io
#import errno
import cv2
import numpy as np
#import functools
from skimage import *
from skimage import color
from skimage.feature import blob_doh
from io import BytesIO
import csv
from time import time

pipeline_obj = object()
sc= object()
spark =object()
npartitions = 8


from scipy.misc import imread, imsave

class ImgPipeline:
    IMG_SERVER = ''
    U_NAME = ''
    PASSWORD = ''
    LOADING_PATH = ''
    SAVING_PATH = ''
    CSV_FILE_PATH = '/home/amit/segment_data/imglist.csv'
    def __init__(self, server, uname, password):
        self.IMG_SERVER = server
        self.U_NAME = uname
        self.PASSWORD = password

    def setLoadAndSavePath(self,loadpath, savepath):
        self.LOADING_PATH = loadpath
        self.SAVING_PATH = savepath

    def setCSVAndSavePath(self,csvpath, savepath):
        self.CSV_FILE_PATH = csvpath
        self.SAVING_PATH = savepath

    def collectDirs(self,apattern = '"*.jpg"'):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.IMG_SERVER, username=self.U_NAME, password=self.PASSWORD)
        ftp = ssh.open_sftp()
        apath = self.LOADING_PATH
        if(apattern=='*' ):
            apattern = '"*"'
        rawcommand = 'find {path} -name {pattern}'
        command = rawcommand.format(path=apath, pattern=apattern)
        stdin, stdout, stderr = ssh.exec_command(command)
        filelist = stdout.read().splitlines()
        print(len(filelist))
        return filelist

    def collectFiles(self, ext):
        files = self.collectDirs(ext)
        filenames = set()
        for file in files:
            if (len(file.split('.')) > 1):
                filenames.add(file)

        filenames = list(filenames)
        return filenames
    def collectImgFromCSV(self, column):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.IMG_SERVER, username=self.U_NAME, password=self.PASSWORD)
        csvfile = None
        try:
            ftp = ssh.open_sftp()

            file = ftp.file(self.CSV_FILE_PATH, "r", -1)
            buf = file.read()
            csvfile = BytesIO(buf)

            ftp.close()
        except IOError as e:
            print(e)
        # ftp.close()
        ssh.close()
        contnts = csv.DictReader(csvfile)
        filenames = {}
        for row in contnts:
            filenames[row[column]] = row[column]
            # filenames.add(row[column])
        return list(filenames)

    def ImgandParamFromCSV(self, column1, column2):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.IMG_SERVER, username=self.U_NAME, password=self.PASSWORD)
        csvfile = None
        try:
            ftp = ssh.open_sftp()

            file = ftp.file(self.CSV_FILE_PATH, "r", -1)
            buf = file.read()
            csvfile = BytesIO(buf)

            ftp.close()
        except IOError as e:
            print(e)
        # ftp.close()
        ssh.close()
        contnts = csv.DictReader(csvfile)
        filenames = {}
        for row in contnts:
            filenames[row[column1]] = row[column2]
            # filenames.add(row[column])
        return filenames

    def collectImgsAsGroup(self, file_abspaths):
        rededge_channel_pattern = re.compile('(.+)_[0-9]+\.tif$')
        # TODO merge this with the RededgeImage object created by Javier.
        image_sets = {}

        for path in file_abspaths:
            match = rededge_channel_pattern.search(path)
            if match:
                common_path = match.group(1)
                if common_path not in image_sets:
                    image_sets[common_path] = []
                image_sets[common_path].append(path)
        grouping_as_dic = dict()
        for grp in image_sets:

            grouping_as_dic.update({grp: image_sets[grp]})
        return grouping_as_dic.items()

    def collectImagesSet(self,ext):

        #Collect sub-directories and files of a given directory
        filelist = self.collectDirs(ext)
        print(len(filelist))
        dirs = set()
        dirs_list = []
        #Create a dictionary that contains: sub-directory --> [list of images of that directory]
        dirs_dict = dict()
        for afile in filelist:
            (head, filename) = os.path.split(afile)
            if (head in dirs):
                if (head != afile):
                    dirs_list = dirs_dict[head]
                    dirs_list.append(afile)
                    dirs_dict.update({head: dirs_list})
            else:
                dirs_list = []
                if (len(filename.split('.')) > 1 and head != afile):
                    dirs_list.append(afile)
                    dirs.add(head)
                    dirs_dict.update({head: dirs_list})

        return dirs_dict.items()


    def loadIntoCluster(self, path, offset=None, size=-1):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.IMG_SERVER, username=self.U_NAME, password=self.PASSWORD)
        imagbuf = ''
        try:
            ftp = ssh.open_sftp()

            file = ftp.file(path, 'r', (-1))
            buf = file.read()
            imagbuf = imread(BytesIO(buf))
            ftp.close()
        except IOError as e:
            print(e)
        # ftp.close()
        ssh.close()
        return (path, imagbuf)

    def loadBundleIntoCluster(self, path, offset=None, size=(-1)):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.IMG_SERVER, username=self.U_NAME, password=self.PASSWORD)
        images = []
        sortedpath= path[1]
        sortedpath.sort()
        print(sortedpath)
        try:
            for img_name in sortedpath:
                ftp = ssh.open_sftp()
                file = ftp.file(img_name, 'r', (-1))
                buf = file.read()
                imagbuf = imread(BytesIO(buf))
                images.append(imagbuf)
                ftp.close()
        except IOError as e:
            print(e)
        ssh.close()
        return (path[0], images)

    def loadBundleIntoCluster_Skip_conversion(self, path, offset=None, size=(-1)):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.IMG_SERVER, username=self.U_NAME, password=self.PASSWORD)
        images = []
        sortedpath= path[1]
        sortedpath.sort()
        print(sortedpath)
        try:
            for img_name in sortedpath:
                ftp = ssh.open_sftp()
                file = ftp.file(img_name, 'r', (-1))
                buf = file.read()
                imagbuf = imread(BytesIO(buf))
                images.append(imagbuf)
                ftp.close()
        except IOError as e:
            print(e)
        ssh.close()
        return (path[0], images,images)


    def convert(self, img_object, params):
        # convert
        gray = cv2.cvtColor(img_object,cv2.COLOR_BGR2GRAY)
        return gray

    def estimate(self,img_object, params):
        knl_size, itns = params
        ret, thresh = cv2.threshold(img_object, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # noise removal
        kernel = np.ones((knl_size, knl_size), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=itns)
        return opening

    def model(self, opening, params):
        knl_size, itns, dstnc, fg_ratio = params
        print(params)
        # sure background area
        kernel = np.ones((knl_size, knl_size), np.uint8)
        sure_bg = cv2.dilate(opening, kernel, iterations=itns)

        # Finding sure foreground area
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, dstnc)
        ret, sure_fg = cv2.threshold(dist_transform, fg_ratio * dist_transform.max(), 255, 0)

        # Finding unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        # Marker labelling
        ret, markers = cv2.connectedComponents(sure_fg)
        print("Number of objects")
        print(ret)
        # Add one to all labels so that sure background is not 0, but 1
        markers = markers + 1

        # Analysis
        # Now, mark the region of unknown with zero
        markers[unknown == 255] = 0
        return markers

    def analysis(self, img_object, markers, params):
        markers = cv2.watershed(img_object, markers)
        img_object[markers == -1] = [255, 0, 0]
        return (img_object, markers)
    def commonTransform(self, datapack, params):
        fname, imgaes = datapack
        procsd_obj=''
        try:
            procsd_obj = self.convert(imgaes, params)
        except Exception as e:
            print(e)

        return (fname, imgaes, procsd_obj)

    def commonEstimate(self, datapack, params):
        fname, img, procsd_obj = datapack
        processed_obj = self.estimate(procsd_obj, params)
        return (fname, img, processed_obj)


    def commonModel(self,datapack, params):

        fname,img, processed_obj = datapack
        model =self.model(processed_obj,params)
        return (fname, img, model)


    def commonAnalysisTransform(self, datapack, params):

        fname, img, model = datapack
        processedimg, stats = self.analysis(img, model, params)
        return (fname, processedimg, stats)


    def extarct_feature_locally(self, feature_name, img):
        if feature_name in ["surf", "SURF"]:
            extractor = cv2.xfeatures2d.SURF_create()
        elif feature_name in ["sift", "SIFT"]:
            extractor = cv2.xfeatures2d.SIFT_create()
        elif feature_name in ["orb", "ORB"]:
            extractor = cv2.ORB_create()
        kp, descriptors = extractor.detectAndCompute(img_as_ubyte(img), None)
        return descriptors

    def estimate_feature(self, img, params):
        feature_name = params
        if feature_name in ["surf", "SURF"]:
            extractor = cv2.xfeatures2d.SURF_create()
        elif feature_name in ["sift", "SIFT"]:
            extractor = cv2.xfeatures2d.SIFT_create()
        elif feature_name in ["orb", "ORB"]:
            extractor = cv2.ORB_create()
        return extractor.detectAndCompute(img_as_ubyte(img), None)

    def saveResult(self, result):
        transport = paramiko.Transport((self.IMG_SERVER, 22))
        transport.connect(username=self.U_NAME, password=self.PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        output = io.StringIO()
        try:
            sftp.stat(self.SAVING_PATH)
        except IOError as e:
            sftp.mkdir(self.SAVING_PATH)

        for lstr in result:
            output.write(str(lstr[0] + "\n", "utf-8"))

        f = sftp.open(self.SAVING_PATH + str("result") + ".txt", 'wb')
        f.write(output.getvalue())

        sftp.close()


    def saveClusterResult(self,result):
         transport = paramiko.Transport((self.IMG_SERVER, 22))
         transport.connect(username=self.U_NAME, password=self.PASSWORD)
         sftp = paramiko.SFTPClient.from_transport(transport)
         # sftp.mkdir("/home/amit/A1/regResult/")
         dirs = set()
         dirs_list = []
         dirs_dict = dict()
         clusters = result
         try:
             sftp.stat(self.SAVING_PATH)
         except IOError as e:
             sftp.mkdir(self.SAVING_PATH)

         for lstr in clusters:
             group = lstr[0][1]
             img_name = lstr[0][0]
             if (group in dirs):
                 exists_list = dirs_dict[group]
                 exists_list.append(img_name)
                 dirs_dict.update({group: exists_list})
             else:
                 dirs_list = []
                 dirs_list.append(img_name)
                 dirs.add(group)
                 dirs_dict.update({group: dirs_list})

         for itms in dirs_dict.items():
             output = io.StringIO()
             for itm in itms[1]:
                 output.write(str(itm + "\n", "utf-8"))

             f = sftp.open(self.SAVING_PATH + str(itms[0]) + ".txt", 'wb')

             f.write(output.getvalue())
         sftp.close()

    def common_write(self, result_path, sftp, fname, img, stat):
        try:
            sftp.stat(result_path)
        except IOError as e:
            sftp.mkdir(result_path)
        buffer = BytesIO()
        imsave(buffer, img, format='PNG')
        buffer.seek(0)
        dirs = fname.split('/')
        print(fname)
        img_name = dirs[len(dirs) - 1]
        only_name = img_name.split('.')
        f = sftp.open(result_path + "/IMG_" + only_name[len(only_name)-2]+".png", 'wb')
        f.write(buffer.read())
        sftp.close()

    def commonSave(self, datapack):
        fname, procsd_img, stats = datapack
        transport = paramiko.Transport((self.IMG_SERVER, 22))
        transport.connect(username=self.U_NAME, password=self.PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        self.common_write(self.SAVING_PATH, sftp, fname, procsd_img, stats)

    def save_img_bundle(self, data_pack):
        (fname, procsdimg, stats) = data_pack
        transport = paramiko.Transport((self.IMG_SERVER, 22))
        transport.connect(username=self.U_NAME, password=self.PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        last_part = fname.split('/')[(len(fname.split('/')) - 1)]
        RESULT_PATH = (self.SAVING_PATH +"/"+ last_part)
        print("Resutl writing into :" + RESULT_PATH)
        try:
            sftp.stat(RESULT_PATH)
        except IOError as e:
            sftp.mkdir(RESULT_PATH)
        for (i, wrapped) in enumerate(procsdimg):
            buffer = BytesIO()
            imsave(buffer, wrapped, format='png')
            buffer.seek(0)
            f = sftp.open(((((RESULT_PATH + '/regi_') + last_part) + str(i)) + '.png'), 'wb')
            f.write(buffer.read())
        sftp.close()

class ImageRegistration(ImgPipeline):
    def convert(self, img, params):

        imgaes = color.rgb2gray(img)
        return imgaes
    def convert_bundle(self, images, params):
        grey_imgs = []
        for img in images:
            try:
                grey_imgs.append(self.convert(img, params))
            except Exception as e:
                print(e)
        return grey_imgs

    def commonTransform(self, datapack, params):

        fname, imgaes = datapack
        procsd_obj=[]
        try:
            procsd_obj = self.convert_bundle(imgaes, params)
        except Exception as e:
           print(e)

        return (fname, imgaes, procsd_obj)


    def bundle_estimate(self, img_obj, params):
        extractor = cv2.xfeatures2d.SIFT_create(nfeatures=100000)
        return extractor.detectAndCompute(img_as_ubyte(img_obj), None)


    def commonEstimate(self, datapack, params):

        fname, imgs, procsd_obj = datapack
        img_key_points = []
        img_descriptors = []
        print("estimatinng for:" + fname + " " + str(len(imgs)))
        for img in procsd_obj:
            try:
                (key_points, descriptors) = self.bundle_estimate(img,params)
                key_points = np.float32([key_point.pt for key_point in key_points])
            except Exception as e:
                descriptors = None
                key_points = None
            img_key_points.append(key_points)
            img_descriptors.append(descriptors)
        procssd_entity = []
        print(str(len(img_descriptors)))
        procssd_entity.append(img_key_points)
        procssd_entity.append(img_descriptors)
        return (fname, imgs, procssd_entity)


    def match_and_tranform(self, keypoints_to_be_reg, features_to_be_reg, ref_keypoints, ref_features, no_of_match,ratio, reproj_thresh):
    #def match_and_tranform(self, features_to_be_reg, keypoints_to_be_reg, ref_features, ref_keypoints, no_of_match, ratio, reproj_thresh):
        matcher = cv2.DescriptorMatcher_create('BruteForce')
        raw_matches = matcher.knnMatch(features_to_be_reg, ref_features, 2)
        matches = [(m[0].trainIdx, m[0].queryIdx) for m in raw_matches if ((len(m) == 2) and (m[0].distance < (m[1].distance * ratio)))]
        back_proj_error = 0
        inlier_count = 0
        H =0
        if (len(matches) > no_of_match):
            src_pts = np.float32([keypoints_to_be_reg[i] for (_, i) in matches])
            dst_pts = np.float32([ref_keypoints[i] for (i, _) in matches])
            (H, status) = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, reproj_thresh)
            src_t = np.transpose(src_pts)
            dst_t = np.transpose(dst_pts)

            for i in range(0, src_t.shape[1]):
                x_i = src_t[0][i]
                y_i = src_t[1][i]
                x_p = dst_t[0][i]
                y_p = dst_t[1][i]
                num1 = (((H[0][0] * x_i) + (H[0][1] * y_i)) + H[0][2])
                num2 = (((H[1][0] * x_i) + (H[1][1] * y_i)) + H[1][2])
                dnm = (((H[2][0] * x_i) + (H[2][1] * y_i)) + H[2][2])
                tmp = (((x_p - (num1 / (dnm ** 2))) + y_p) - (num2 / (dnm ** 2)))
                if (status[i] == 1):
                    back_proj_error += tmp
                    inlier_count += 1
        return (back_proj_error, inlier_count, H)
    def wrap_and_sample(self, transformed_img, ref_img):
        wrapped = cv2.warpPerspective(ref_img, transformed_img, (ref_img.shape[1], ref_img.shape[0]))
        return wrapped

    def commonModel(self,datapack, params):

        fname,imgs, procssd_entity = datapack
        right_key_points = procssd_entity[0]
        img_features = procssd_entity[1]
        no_of_match, ratio, reproj_thresh, base_img_idx = params
        indx = 0
        Hs = []
        back_proj_errors = []
        inlier_counts = []
        #imgs = []
        print("Modeling for:"+str(len(imgs)))
        for imgind, right_features in enumerate(img_features):
            if (right_features != None):
                #imgs.append(img[imgind])
                (back_proj_error, inlier_count, H) = self.match_and_tranform(right_key_points[imgind], right_features, right_key_points[base_img_idx], img_features[base_img_idx], no_of_match, ratio, reproj_thresh)
                if ((H != None)):
                    Hs.append(H)
                    back_proj_errors.append(back_proj_error)
                    inlier_counts.append(inlier_count)
                else:
                    print("Algorithm is not working properly")
            print("it is working:" + str(imgind))
            indx = (indx + 1)
        Hs.insert(base_img_idx, np.identity(3))
        model = []
        model.append(Hs)
        model.append(back_proj_errors)
        model.append(inlier_counts)
        return (fname, imgs, model)


    def commonAnalysisTransform(self, datapack, params):

        (fname, imgs, model) = datapack
        H = model[0]
        wrappeds = []
        if(len(H) <1):
            print("H is empty algorithm is not working properly")
        for i, img in enumerate(imgs):
            wrapped = self.wrap_and_sample(H[i], img)
            wrappeds.append(wrapped)
        stats = []
        stats.append(H)
        stats.append(model[1])
        stats.append(model[2])
        return (fname, wrappeds, stats)


    def write_register_images(self, data_pack):
        (fname, procsdimg, stats) = data_pack
        transport = paramiko.Transport((self.IMG_SERVER, 22))
        transport.connect(username=self.U_NAME, password=self.PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        RESULT_PATH = (self.SAVING_PATH +"/"+ fname.split('/')[(len(fname.split('/')) - 1)])
        print("Resutl writing into :" + RESULT_PATH)
        try:
            sftp.stat(RESULT_PATH)
        except IOError as e:
            sftp.mkdir(RESULT_PATH)
        for (i, wrapped) in enumerate(procsdimg):
            buffer = BytesIO()
            imsave(buffer, wrapped, format='PNG')
            buffer.seek(0)
            f = sftp.open((((((RESULT_PATH + '/IMG_') + '0') + '_') + str(i)) + '.png'), 'wb')
            f.write(buffer.read())
        sftp.close()


class ImageStitching(ImgPipeline):
    def convert(self, img, params):
        if(len(img.shape) == 3):
            imgaes = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            imgaes = img
        return imgaes

    def convert_bundle(self, images, params):
        grey_imgs = []
        for img in images:
            try:
                grey_imgs.append(self.convert(img, params))
            except Exception as e:
                print(e)
        return grey_imgs

    def commonTransform(self, datapack, params):

        fname, images = datapack
        print("size: %", params)
        resize_imgs = []
        for img in images:
            resize_imgs.append(cv2.resize(img,params))
        procsd_obj=[]
        try:
            procsd_obj = self.convert_bundle(resize_imgs, params)
        except Exception as e:
           print(e)

        return (fname, resize_imgs, procsd_obj)


    def bundle_estimate(self, img_obj, params):
        extractor = cv2.xfeatures2d.SURF_create()
        return extractor.detectAndCompute(img_as_ubyte(img_obj), None)


    def commonEstimate(self, datapack, params):

        fname, imgs, procsd_obj = datapack
        img_key_points = []
        img_descriptors = []
        print("estimatinng for:" + fname + " " + str(len(imgs)))
        for img in procsd_obj:
            try:
                (key_points, descriptors) = self.bundle_estimate(img,params)

            except Exception as e:
                descriptors = None
                key_points = None
            img_key_points.append(key_points)
            img_descriptors.append(descriptors)
        procssd_entity = []
        print(str(len(img_descriptors)))
        procssd_entity.append(img_key_points)
        procssd_entity.append(img_descriptors)
        return (fname, imgs, procssd_entity)

    def match(self, img_to_merge, feature, kp):
        index_params = dict(algorithm=0, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        kp_to_merge, feature_to_merge = self.getFeatureOfMergedImg(img_to_merge)
        matches = flann.knnMatch(feature,feature_to_merge,k=2)

        good = []
        for i, (m, n) in enumerate(matches):
            if m.distance < 0.7 * n.distance:
                good.append((m.trainIdx, m.queryIdx))

        if len(good) > 4:
            pointsCurrent = kp
            pointsPrevious = kp_to_merge

            matchedPointsCurrent = np.float32([pointsCurrent[i].pt for (__, i) in good])
            matchedPointsPrev = np.float32([pointsPrevious[i].pt for (i, __) in good])

        H, s = cv2.findHomography(matchedPointsCurrent, matchedPointsPrev, cv2.RANSAC, 4)
        return H

    def match2(self, img_to_merge, b):
        index_params = dict(algorithm=0, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        kp_to_merge, feature_to_merge = self.getFeatureOfMergedImg(img_to_merge)
        bkp, bf  = self.getFeatureOfMergedImg(b)
        matches = flann.knnMatch(bf, feature_to_merge, k=2)

        good = []
        for i, (m, n) in enumerate(matches):
            if m.distance < 0.7 * n.distance:
                good.append((m.trainIdx, m.queryIdx))

        if len(good) > 4:
            pointsCurrent = bkp
            pointsPrevious = kp_to_merge

            matchedPointsCurrent = np.float32([pointsCurrent[i].pt for (__, i) in good])
            matchedPointsPrev = np.float32([pointsPrevious[i].pt for (i, __) in good])

        H, s = cv2.findHomography(matchedPointsCurrent, matchedPointsPrev, cv2.RANSAC, 4)
        return H

    def getFeatureOfMergedImg(self, img):
        grey = self.convert(img,(0))
        return self.bundle_estimate(grey, (0))

    def commonModel(self,datapack, params):

        fname,imgs, procssd_entity = datapack
        right_key_points = procssd_entity[0]
        img_features = procssd_entity[1]
        mid_indx = int(len(imgs)/2)
        start_indx = 1
        frst_img = imgs[0]
        print("shape of first img: % ", frst_img.shape)
        print("first phase {} ".format(mid_indx))
        for idx in range(mid_indx):
            H = self.match(frst_img, img_features[start_indx], right_key_points[start_indx])
            #H = self.match2(frst_img, imgs[start_indx])
            xh = np.linalg.inv(H)

            if(len(frst_img.shape) == 3):
                ds = np.dot(xh, np.array([frst_img.shape[1], frst_img.shape[0], 1]))
                ds = ds / ds[-1]
                print("final ds=>", ds)
                f1 = np.dot(xh, np.array([0, 0, 1]))
                f1 = f1 / f1[-1]
                xh[0][-1] += abs(f1[0])
                xh[1][-1] += abs(f1[1])
                ds = np.dot(xh, np.array([frst_img.shape[1], frst_img.shape[0], 1]))
            else:
                ds = np.dot(xh, np.array([frst_img.shape[1], frst_img.shape[0],1]))
                print(ds[-1])
                ds = ds / ds[-1]
                print("final ds=>", ds)
                f1 = np.dot(xh, np.array([0, 0,1]))
                f1 = f1 / f1[-1]
                xh[0][-1] += abs(f1[0])
                xh[1][-1] += abs(f1[1])
                ds = np.dot(xh, np.array([frst_img.shape[1], frst_img.shape[0],1]))
            offsety = abs(int(f1[1]))
            offsetx = abs(int(f1[0]))
            dsize = (int(ds[0]) + offsetx, int(ds[1]) + offsety)
            print("image dsize =>", dsize) #(697, 373)
            tmp = cv2.warpPerspective(frst_img, xh, (frst_img.shape[1] * 2, frst_img.shape[0] * 2))
            # cv2.imshow("warped", tmp)
            # cv2.waitKey()
            print("shape of img: %", imgs[start_indx].shape)
            print("shape of new {}".format(tmp.shape))

            tmp[offsety:imgs[start_indx].shape[0] + offsety, offsetx:imgs[start_indx].shape[1] + offsetx] = imgs[start_indx]
            frst_img = tmp
            start_indx = start_indx + 1
        model = []
        model.append(frst_img)
        model.append(procssd_entity)

        return (fname, imgs, model)

    # Homography is:  [[8.86033773e-01   6.59154846e-02   1.73593010e+02]
    #                  [-8.13825392e-02   9.77171622e-01 - 1.25890876e+01]
    # [-2.61821451e-04
    # 4.91986599e-05
    # 1.00000000e+00]]
    # Inverse
    # Homography: [[1.06785933e+00 - 6.26599825e-02 - 1.86161748e+02]
    #              [9.24787290e-02   1.01728698e+00 - 3.24694609e+00]
    # [2.75038650e-04 - 6.64548835e-05
    # 9.51418606e-01]]
    # final
    # ds = > [288.42753648  345.21227814    1.]
    # image
    # dsize = > (697, 373)
    # shape
    # of
    # new(373, 697, 3)

    def commonAnalysisTransform(self, datapack, params):

        fname, imgs, model = datapack
        procssd_entity = model[1]
        right_key_points = procssd_entity[0]
        img_features = procssd_entity[1]
        mid_indx = int(len(imgs) / 2)
        length = len(imgs)
        start_indx = mid_indx
        frst_img = model[0]
        print("second phase: %", start_indx)
        for idx in range(length-mid_indx):
            H = self.match(frst_img, img_features[start_indx], right_key_points[start_indx])

            txyz = np.dot(H, np.array([imgs[start_indx].shape[1], imgs[start_indx].shape[0], 1]))
            txyz = txyz / txyz[-1]
            dsize = (int(txyz[0]) + frst_img.shape[1], int(txyz[1]) + frst_img.shape[0])
            tmp = cv2.warpPerspective(imgs[start_indx], H, dsize)
            # tmp[:self.leftImage.shape[0], :self.leftImage.shape[1]]=self.leftImage
            tmp = self.mix_and_match(frst_img, tmp)
            frst_img = tmp
            start_indx = start_indx + 1

        return (fname, frst_img, '')


    def mix_and_match(self, leftImage, warpedImage):
        i1y, i1x = leftImage.shape[:2]
        i2y, i2x = warpedImage.shape[:2]
        print(leftImage[-1, -1])

        black_l = np.where(leftImage == np.array([0, 0, 0]))
        black_wi = np.where(warpedImage == np.array([0, 0, 0]))
        for i in range(0, i1x):
            for j in range(0, i1y):
                try:
                    if (np.array_equal(leftImage[j, i], np.array([0, 0, 0])) and np.array_equal(warpedImage[j, i],
                                                                                                np.array([0, 0, 0]))):
                        # print "BLACK"
                        # instead of just putting it with black,
                        # take average of all nearby values and avg it.
                        warpedImage[j, i] = [0, 0, 0]
                    else:
                        if (np.array_equal(warpedImage[j, i], [0, 0, 0])):
                            # print "PIXEL"
                            warpedImage[j, i] = leftImage[j, i]
                        else:
                            if not np.array_equal(leftImage[j, i], [0, 0, 0]):
                                bw, gw, rw = warpedImage[j, i]
                                bl, gl, rl = leftImage[j, i]
                                # b = (bl+bw)/2
                                # g = (gl+gw)/2
                                # r = (rl+rw)/2
                                warpedImage[j, i] = [bl, gl, rl]
                except:
                    pass
        # cv2.imshow("waRPED mix", warpedImage)
        # cv2.waitKey()
        return warpedImage

    def write_stitch_images(self, data_pack):
        (fname, procsdimg, stats) = data_pack
        transport = paramiko.Transport((self.IMG_SERVER, 22))
        transport.connect(username=self.U_NAME, password=self.PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        RESULT_PATH = (self.SAVING_PATH +"/"+ fname.split('/')[(len(fname.split('/')) - 1)])
        print("Resutl writing into :" + RESULT_PATH)
        try:
            sftp.stat(RESULT_PATH)
        except IOError as e:
            sftp.mkdir(RESULT_PATH)

        buffer = BytesIO()
        imsave(buffer, procsdimg, format='PNG')
        buffer.seek(0)
        f = sftp.open((((((RESULT_PATH + '/IMG_') + '0') + '_') + "stitched") + '.png'), 'wb')
        f.write(buffer.read())
        sftp.close()


class FlowerCounter(ImgPipeline):
    common_size =(534, 800)
    region_matrix = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    template_img = []
    avrg_histo_b = []
    def setTemplateandSize(self, img, size):
        self.common_size = size
        self.template_img=img

    def setRegionMatrix(self, mat):
        self.region_matrix = mat

    def setAvgHist(self, hist):
        self.avrg_histo_b = hist

    def convert(self, img_obj, params):
        img_asarray = np.array(img_obj)
        return img_asarray



    def getFlowerArea(self, img, hist_b_shifts, segm_B_lower, segm_out_value=0.99, segm_dist_from_zerocross=5):
        """
        Take the image given as parameter and highlight flowers applying a logistic function
        on the B channel. The formula applied is f(x) = 1/(1 + exp(K * (x - T))) being K and T constants
        calculated based on the given parameters.
        :param img: Image array
        :param fname: Image filename
        :param segm_out_value: Value of the logistic function output when the input is the lower B segmentation value i.e. f(S), where S = self.segm_B_lower + self.hist_b_shifts[fname]
        :param segm_dist_from_zerocross: Value that, when substracted from the lower B segmentation value, the output is 0.5 i.e. Value P where f(self.segm_B_lower + self.hist_b_shifts[fname] - P) = 0.5
        :return: Grayscale image highlighting flower pixels (pixels values between 0 and 1)
        """
        # Convert to LAB
        img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)

        # Get the B channel and convert to float
        img_B = np.array(img_lab[:, :, 2], dtype=np.float32)

        # Get the parameter T for the formula
        print(segm_dist_from_zerocross)
        t_exp = float(segm_B_lower) + float(hist_b_shifts) - float(segm_dist_from_zerocross)

        # Get the parameter K for the formula
        k_exp = np.log(1 / segm_out_value - 1) / segm_dist_from_zerocross

        # Apply logistic transformation
        img_B = 1 / (1 + np.exp(k_exp * (img_B - t_exp)))

        return img_B

    def estimate(self, img_object, params):
        plot_mask = params

        array_image = np.asarray(img_object)
        im_bgr = np.array(array_image)
        # Shift to grayscale
        im_gray = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2GRAY)

        # Shift to LAB
        im_lab_plot = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2Lab)

        # Keep only plot pixels
        im_gray = im_gray[plot_mask > 0]
        im_lab_plot = im_lab_plot[plot_mask > 0]

        # Get histogram of grayscale image
        hist_G, _ = np.histogram(im_gray, 256, [0, 256])

        # Get histogram of B component
        hist_b, _ = np.histogram(im_lab_plot[:, 2], 256, [0, 256])
        histograms = []
        histograms.append(hist_b)
        histograms.append(hist_G)
        return histograms

    def model(self,processed_obj, params):
        hist_b = processed_obj[0]
        avg_hist_b = params
        # Calculate correlation
        correlation_b = np.correlate(hist_b, avg_hist_b, "full")

        # Get the shift on the X axis
        x_shift_b = correlation_b.argmax().astype(np.int8)
        return x_shift_b

    def analysis(self, img, model, params):
        flower_area_mask, segm_B_lower = params
        hist_b_shift = model
        # Get flower mask for this image

        # pil_image = PIL.Image.open(value).convert('RGB')
        open_cv_image = np.array(img)
        # print open_cv_image
        # img = open_cv_image[::-1].copy()
        img = open_cv_image[:, :, ::-1].copy()

        # Highlight flowers
        img_flowers = self.getFlowerArea(img, hist_b_shift, segm_B_lower, segm_dist_from_zerocross=8)

        # Apply flower area mask
        # print(img_flowers)
        # print(flower_area_mask)
        img_flowers[flower_area_mask == 0] = 0

        # Get number of flowers using blob counter on the B channel
        blobs = blob_doh(img_flowers, max_sigma=5, min_sigma=1)
        for bld in blobs:
            x, y, r = bld
            cv2.circle(img, (int(x), int(y)), int(r + 1), (0, 0, 0), 1)
        return (img, blobs)

    def crossProduct(self, p1, p2, p3):
        """
        Cross product implementation: (P2 - P1) X (P3 - P2)
        :param p1: Point #1
        :param p2: Point #2
        :param p3: Point #3
        :return: Cross product
        """
        v1 = [p2[0] - p1[0], p2[1] - p1[1]]
        v2 = [p3[0] - p2[0], p3[1] - p2[1]]
        return v1[0] * v2[1] - v1[1] * v2[0]

    def userDefinePlot(self, img, bounds=None):
        """

        :param image: The image array that contains the crop
        :param bounds: Optionally user can set up previously the bounds without using GUI
         :return: The four points selected by user and the mask to apply to the image
        """
        # Initial assert
        if not isinstance(img, np.ndarray):
            print("Image is not a numpy array")
            return

        # Get image shape
        shape = img.shape[::-1]

        # Eliminate 3rd dimension if image is colored
        if len(shape) == 3:
            shape = shape[1:]

        # Function definitions
        def getMask(boundM):
            """
            Get mask from bounds
            :return: Mask in a numpy array
            """
            # Initialize mask
            # shapeM = img.shape[1::-1]
            mask = np.zeros(shape[::-1])

            # Get boundaries of the square containing our ROI
            minX = max([min([x[0] for x in boundM]), 0])
            minY = max([min([y[1] for y in boundM]), 0])
            maxX = min(max([x[0] for x in boundM]), shape[0])
            maxY = min(max([y[1] for y in boundM]), shape[1])

            # Reshape bounds
            # boundM = [(minX, minY), (maxX, minY), (minX, maxY), (maxX, maxY)]

            # Iterate through the containing-square and eliminate points
            # that are out of the ROI
            for x in range(minX, maxX):
                for y in range(minY, maxY):
                    h1 = self.crossProduct(boundM[2], boundM[0], (x, y))
                    h2 = self.crossProduct(boundM[3], boundM[1], (x, y))
                    v1 = self.crossProduct(boundM[0], boundM[1], (x, y))
                    v2 = self.crossProduct(boundM[2], boundM[3], (x, y))
                    if h1 > 0 and h2 < 0 and v1 > 0 and v2 < 0:
                        mask[y, x] = 255

            return mask

        # Check if bounds have been provided
        if isinstance(bounds, list):
            if len(bounds) != 4:
                print("Bounds length must be 4. Setting up GUI...")
            else:
                mask = getMask(bounds)
                return bounds, mask

        # Get image shape
        # shape = img.shape[1::-1]

        # Initialize boudaries
        height,width = self.common_size
        bounds = [(0, 0), ((height-1), 0), (0, (width-1)), ((height-1), (width-1))]

        # if plot == False:
        #    #for flower area
        #    bounds = [(308, 247), (923, 247), (308, 612), (923, 612)]


        # Get binary mask for the user-selected ROI
        mask = getMask(bounds)

        return bounds, mask

    # filenames = list_files("/data/mounted_hdfs_path/user/hduser/plot_images/2016-07-05_1207")


    def setPlotMask(self, bounds, imsize, mask=None):
        """
        Set mask of the plot under analysis
        :param mask: Mask of the plot
        :param bounds: Bounds of the plot
        """
        plot_bounds = None
        plot_mask = None
        # Initial assert
        if mask is not None:
            print(mask.shape)
            print(imsize)
            assert isinstance(mask, np.ndarray), "Parameter 'corners' must be Numpy array"
            assert mask.shape == imsize, "Mask has a different size"
        assert isinstance(bounds, list) and len(bounds) == 4, "Bounds must be a 4-element list"

        # Store bounds
        plot_bounds = bounds

        # Store mask
        if mask is None:
            _, plot_mask = self.userDefinePlot(np.zeros(imsize), bounds)

        else:
            plot_mask = mask

        return plot_bounds, plot_mask

    def setFlowerAreaMask(self, region_matrix, mask, imsize):
        """
        Set mask of the flower area within the plot
        :param region_matrix = Region matrix representing the flower area
        :param mask: Mask of the flower area
        """

        # Initial assert
        if mask is not None:
            assert isinstance(mask, np.ndarray), "Parameter 'mask' must be Numpy array"
            assert mask.shape == imsize, "Mask has a different size"

        # assert isinstance(bounds, list) and len(bounds) == 4, "Bounds must be a 4-element list"

        # Store bounds
        flower_region_matrix = region_matrix

        # Store mask
        flower_area_mask = mask

        return flower_area_mask

    def calculatePlotMask(self, images_bytes, imsize):
        """
        Compute plot mask
        """
        # Trace
        print("Computing plot mask...")

        # Read an image

        open_cv_image = np.array(images_bytes)

        # print open_cv_image
        # print (open_cv_image.shape)
        # Convert RGB to BGR
        # open_cv_image = open_cv_image[:, :, ::-1].copy()


        p_bounds, p_mask = self.userDefinePlot(open_cv_image, None)

        # Store mask and bounds
        return self.setPlotMask(p_bounds, imsize, p_mask)

    def calculateFlowerAreaMask(self, region_matrix, plot_bounds, imsize):
        """
        Compute the flower area mask based on a matrix th        for bld in blob:
            x, y, r = bld
            cv2.circle(img, (int(x), int(y)), int(r + 1), (0, 0, 0), 1)at indicates which regions of the plot are part of the
        flower counting.
        :param region_matrix: Mmatrix reflecting which zones are within the flower area mask (e.g. in order to
        sample the center region, the matrix should be [[0,0,0],[0,1,0],[0,0,0]]
        """

        # Trace
        print("Computing flower area mask...")

        # Check for plot bounds
        assert len(plot_bounds) > 0, "Plot bounds not set. Please set plot bounds before setting flower area mask"

        # Convert to NumPy array if needed
        if not isinstance(region_matrix, np.ndarray):
            region_matrix = np.array(region_matrix)

        # Assert
        assert region_matrix.ndim == 2, 'region_matrix must be a 2D matrix'

        # Get the number of rows and columns in the region matrix
        rows, cols = region_matrix.shape

        # Get transformation matrix
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [cols, 0], [0, rows], [cols, rows]]),
                                        np.float32(plot_bounds))

        # Initialize flower area mask
        fw_mask = np.zeros(imsize)

        # Go over the flower area mask and turn to 1 the marked areas in the region_matrix
        for x in range(cols):
            for y in range(rows):
                # Write a 1 if the correspondant element in the region matrix is 1
                if region_matrix[y, x] == 1:
                    # Get boundaries of this zone as a float32 NumPy array
                    bounds = np.float32([[x, y], [x + 1, y], [x, y + 1], [x + 1, y + 1]])
                    bounds = np.array([bounds])

                    # Transform points
                    bounds_T = cv2.perspectiveTransform(bounds, M)[0].astype(np.int)

                    # Get mask for this area
                    _, mask = self.userDefinePlot(fw_mask, list(bounds_T))

                    # Apply mask
                    fw_mask[mask > 0] = 255

        # Save flower area mask & bounds
        return self.setFlowerAreaMask(region_matrix, fw_mask, imsize)

    def computeAverageHistograms(self, hist_b_all):
        """
        Compute average B histogram
        """
        # Vertically stack all the B histograms
        avg_hist_B = np.vstack(tuple([h for h in hist_b_all]))

        # Sum all columns
        avg_hist_B = np.sum(avg_hist_B, axis=0)

        # Divide by the number of images and store
        avg_hist_b = np.divide(avg_hist_B, len(hist_b_all))

        return avg_hist_b
    def common_write(self, result_path, sftp, fname, img, stat):
        try:
            sftp.stat(result_path)
        except IOError as e:
            sftp.mkdir(result_path)
        buffer = BytesIO()
        imsave(buffer, img, format='PNG')
        buffer.seek(0)
        dirs = fname.split('/')
        print(fname)
        img_name = dirs[len(dirs) - 1]
        only_name = img_name.split('.')
        f = sftp.open(result_path + "/IMG_" + only_name[len(only_name)-2]+".png", 'wb')
        f.write(buffer.read())
        sftp.close()

class PlotSegment(ImgPipeline):

    def normalize_gaps(self, gaps, num_items):
        gaps = list(gaps)

        gaps_arr = np.array(gaps, dtype=np.float64)
        if gaps_arr.shape == (1,):
            gap_size = gaps_arr[0]
            gaps_arr = np.empty(num_items - 1)
            gaps_arr.fill(gap_size)
        elif gaps_arr.shape != (num_items - 1,):
            raise ValueError('gaps should have shape {}, but has shape {}.'
                             .format((num_items - 1,), gaps_arr.shape))
        return gaps_arr

    def get_repeated_seqs_2d_array(self, buffer_size, item_size, gaps, num_repeats_of_seq):
        start = buffer_size
        steps = gaps + item_size
        items = np.insert(np.cumsum(steps), 0, np.array(0)) + start
        return np.tile(items, (num_repeats_of_seq, 1))

    def set_plot_layout_relative_meters(self, buffer_blocwise_m, plot_width_m, gaps_blocs_m, num_plots_per_bloc, buffer_plotwise_m, plot_height_m, gaps_plots_m, num_blocs):

        # this one already has the correct grid shape.
        plot_top_left_corners_x = self.get_repeated_seqs_2d_array(buffer_blocwise_m, plot_width_m, gaps_blocs_m, num_plots_per_bloc)
        # this one needs to be transposed to assume the correct grid shape.
        plot_top_left_corners_y = self.get_repeated_seqs_2d_array(buffer_plotwise_m, plot_height_m, gaps_plots_m, num_blocs).T

        num_plots = num_blocs * num_plots_per_bloc
        plot_top_left_corners = np.stack((plot_top_left_corners_x, plot_top_left_corners_y)).T.reshape((num_plots, 2))

        plot_height_m_buffered = plot_height_m - 2 * buffer_plotwise_m
        plot_width_m_buffered = plot_width_m - 2 * buffer_blocwise_m

        plot_top_right_corners = np.copy(plot_top_left_corners)

        plot_top_right_corners[:, 0] = plot_top_right_corners[:, 0] + plot_width_m_buffered

        plot_bottom_left_corners = np.copy(plot_top_left_corners)
        plot_bottom_left_corners[:, 1] = plot_bottom_left_corners[:, 1] + plot_height_m_buffered

        plot_bottom_right_corners = np.copy(plot_top_left_corners)

        plot_bottom_right_corners[:, 0] = plot_bottom_right_corners[:, 0] + plot_width_m_buffered

        plot_bottom_right_corners[:, 1] = plot_bottom_right_corners[:, 1] + plot_height_m_buffered

        plots_all_box_coords = np.concatenate((plot_top_left_corners, plot_top_right_corners,
                                               plot_bottom_right_corners, plot_bottom_left_corners), axis=1)
        print(plots_all_box_coords)
        plots_corners_relative_m = plots_all_box_coords
        return plots_corners_relative_m

    def plot_segmentation(self, num_blocs, num_plots_per_bloc, plot_width, plot_height):
        # num_blocs = 5
        # num_plots_per_bloc = 17
        gaps_blocs = np.array([50])
        gaps_plots = np.array([5])
        buffer_blocwise = 1
        buffer_plotwise = 1
        # plot_width = 95
        # plot_height = 30


        num_blocs = int(num_blocs)
        num_plots_per_bloc = int(num_plots_per_bloc)
        buffer_blocwise_m = float(buffer_blocwise)
        buffer_plotwise_m = float(buffer_plotwise)
        plot_width_m = float(plot_width)
        plot_height_m = float(plot_height)

        if not all((num_blocs >= 1,
                    num_plots_per_bloc >= 1,
                    buffer_blocwise_m >= 0,
                    buffer_plotwise_m >= 0,
                    plot_width_m >= 0,
                    plot_height_m >= 0)):
            raise ValueError("invalid field layout parameters.")

        gaps_blocs_m = self.normalize_gaps(gaps_blocs, num_blocs)
        print(gaps_blocs_m)
        gaps_plots_m = self.normalize_gaps(gaps_plots, num_plots_per_bloc)
        print(gaps_plots_m)
        plots_corners_relative_m = None

        return self.set_plot_layout_relative_meters(buffer_blocwise_m, plot_width_m, gaps_blocs_m, num_plots_per_bloc, buffer_plotwise_m, plot_height_m, gaps_plots_m, num_blocs)

    def estimate(self,img_object, params):
        num_blocs, num_plots_per_bloc, p_width, p_height = params
        coord = self.plot_segmentation(num_blocs, num_plots_per_bloc, p_width, p_height)
        return coord

    def analysis(self, img, coord, params):

        xOffset, yOffset = params
        for i in range(coord.shape[0]):
            cv2.line(img, (int(coord[i, 0] + xOffset), int(coord[i, 1] + yOffset)),
                     (int(coord[i, 2] + xOffset), int(coord[i, 3] + yOffset)), (255, 255, 255), 2)
            cv2.line(img, (int(coord[i, 2] + xOffset), int(coord[i, 3] + yOffset)),
                     (int(coord[i, 4] + xOffset), int(coord[i, 5] + yOffset)), (255, 255, 255), 2)
            cv2.line(img, (int(coord[i, 4] + xOffset), int(coord[i, 5] + yOffset)),
                     (int(coord[i, 6] + xOffset), int(coord[i, 7] + yOffset)), (255, 255, 255), 2)
            cv2.line(img, (int(coord[i, 6] + xOffset), int(coord[i, 7] + yOffset)),
                     (int(coord[i, 0] + xOffset), int(coord[i, 1] + yOffset)), (255, 255, 255), 2)
        return (img, params)

    def commonEstimate(self, datapack, params):
        fname, img = datapack
        get_params = params[fname]
        extract_param = get_params.split()
        processed_obj = self.estimate(None, (int(extract_param[0]),int(extract_param[1]), int(extract_param[2]), int(extract_param[3]) ))
        return (fname, img, processed_obj)

    def commonAnalysisTransform(self, datapack, params):

        fname, img, model = datapack
        get_params = params[fname]
        extract_param = get_params.split()
        processedimg, stats = self.analysis(img, model,(int(extract_param[4]), int(extract_param[5])))
        return (fname, processedimg, stats)

#print(filenames)
#ftp = sc.broadcast(ftp)
def collectFiles(pipes, pattern):

    fil_list = pipes.collectFiles(pattern)
    return fil_list

def collectfromCSV(pipes, column):
    fil_list = pipes.collectImgFromCSV(column)
    return fil_list
def loadFiles( pipes, fil_list):
    images = []
    for file_path in fil_list:
        images.append(pipes.loadIntoCluster(file_path))
    return images

def collectResultAsName(pipes, rdd):
    pipes.saveResult(rdd.collect())

def collectBundle(pipes, pattern):
    image_sets_dirs = pipes.collectImagesSet(pattern)
    return image_sets_dirs

def loadBundle( pipes, fil_list):
    bundles = []
    for sub_path in fil_list:
        print(sub_path[0])
        print(sub_path[1])
        bundles.append( pipes.loadBundleIntoCluster(sub_path))
    return bundles

def loadBundleSkipConvert( pipes, fil_list):
    bundles = []
    for sub_path in fil_list:
        print(sub_path[0])
        print(sub_path[1])
        bundles.append( pipes.loadBundleIntoCluster_Skip_conversion(sub_path))
    return bundles

def img_registration(sc, server, uname, password, data_path, save_path, img_type, no_of_match, ratio, reproj_thresh, base_img_idx):
    print('Executing from web................')
    pipes = ImageRegistration(server, uname, password)
    pipes.setLoadAndSavePath(data_path, save_path)
    file_bundles = collectBundle(pipes, img_type)
    rdd = loadBundle(pipes, file_bundles)
    processing_start_time = time()
    for bundle in rdd:
        pack = pipes.commonTransform(bundle, (0))
        pack = pipes.commonEstimate( pack, ('sift'))

        pack = pipes.commonModel(pack, (no_of_match, ratio, reproj_thresh, base_img_idx))
        pack = pipes.commonAnalysisTransform(pack, (0))
        pipes.write_register_images(pack)
    processing_end_time = time() - processing_start_time
    print( "SUCCESS: Images procesed in {} seconds".format(round(processing_end_time, 3)))

def img_registration2(sc, server, uname, password, data_path, save_path, img_type, no_of_match, ratio, reproj_thresh, base_img_idx):
    print('Executing from web................')
    pipes = ImageRegistration(server, uname, password)
    pipes.setLoadAndSavePath(data_path, save_path)
    file_bundles = pipes.collectImgsAsGroup(pipes.collectDirs(img_type))
    rdd = loadBundleSkipConvert(pipes, file_bundles)
    processing_start_time = time()
    for bundle in rdd:
        pack = pipes.commonEstimate( bundle, ('sift'))
        pack = pipes.commonModel(pack, (no_of_match, ratio, reproj_thresh, base_img_idx))
        pack = pipes.commonAnalysisTransform(pack, (0))
        pipes.save_img_bundle(pack)
    processing_end_time = time() - processing_start_time
    print( "SUCCESS: Images procesed in {} seconds".format(round(processing_end_time, 3)))

def img_segmentation(sc,server,uname,upass, data_path, save_path, img_type,kernel_size, iterations, distance, forg_ratio):
    pipes = ImgPipeline(server, uname, upass)
    pipes.setLoadAndSavePath(data_path, save_path)
    files = collectFiles(pipes, img_type)
    rdd = loadFiles(pipes, files)
    processing_start_time = time()
    for bundle in rdd:
        pack = pipes.commonTransform(bundle, (0))
        pack = pipes.commonEstimate( pack, (kernel_size,iterations))

        pack = pipes.commonModel(pack, (kernel_size, iterations, distance, forg_ratio))
        pack = pipes.commonAnalysisTransform(pack, (0))
        pipes.commonSave(pack)
    processing_end_time = time() - processing_start_time
    print("SUCCESS: Images procesed in {} seconds".format(round(processing_end_time, 3)))

#127.0.0.1 akm523 523@mitm /hadoopdata/segment_data /hadoopdata/segment_result '*' 3 2 0 .70

def callImgSeg():
    try:
        print(sys.argv[1:8])
        server = sys.argv[1]
        uname = sys.argv[2]
        upass = sys.argv[3]
        print('From web .............')
        print(uname)
        data_path = sys.argv[4]
        save_path = sys.argv[5]
        img_type = sys.argv[6]
        kernel_size = int(sys.argv[7])
        iterations = int(sys.argv[8])
        distance = int(sys.argv[9])
        fg_ratio = float(sys.argv[10])
        img_segmentation(sc, server, uname, upass, data_path, save_path, img_type, kernel_size, iterations, distance,
                         fg_ratio)

    except Exception as e:
        print(e)
        # img_matching(sc, server, uname, upass, data_path, save_path, img_type, img_to_seacrh, ratio = 0.55)
        # img_clustering(sc, server, uname, upass, csv_path, save_path, "'*'", K=3, iterations=20)

#127.0.0.1 akm523 523@mitm /hadoopdata/reg_test_images /result '*' 4 .75 0 0
def callImgReg():
    print(sys.argv[2:12])
    server = sys.argv[2]
    uname = sys.argv[3]
    upass = sys.argv[4]
    print('From web .............')
    print(uname)
    data_path = sys.argv[5]
    save_path = sys.argv[6]
    img_type = sys.argv[7]
    no_of_match = int(sys.argv[8])
    ratio = float(sys.argv[9])
    reproj_thresh = float(sys.argv[10])
    base_img_idx = int(sys.argv[11])
    #img_registration(sc, server, uname, upass, data_path, save_path, img_type, no_of_match, ratio, reproj_thresh, base_img_idx)
    img_registration2(sc, server, uname, upass, data_path, save_path, img_type, no_of_match, ratio, reproj_thresh, base_img_idx)

#127.0.0.1 uname pass /hadoopdata/flower /hadoopdata/flower_result '*' 155
def callFlowerCount():
    print(sys.argv[1:8])
    server = sys.argv[1]
    uname = sys.argv[2]
    upass = sys.argv[3]
    print('From web .............')
    print(uname)
    data_path = sys.argv[4]
    save_path = sys.argv[5]
    img_type = sys.argv[6]
    segm_B_lower = int(sys.argv[7])

    pipes = FlowerCounter(server, uname, upass)
    pipes.setLoadAndSavePath(data_path, save_path)
    files = collectFiles(pipes, img_type)
    print(files[0:20])
    rdd = loadFiles(pipes, files[0:20])
    packs = []
    processing_start_time = time()
    for bundle in rdd:
        packs.append(pipes.commonTransform(bundle, (0)))

    template = packs[0]
    print(len(template))
    tem_img = template[2]
    height, width,channel = tem_img.shape
    pipes.setTemplateandSize(tem_img, (height, width))
    region_matrix = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    pipes.setRegionMatrix(region_matrix)
    print(len(tem_img), tem_img.shape)
    plot_bound, plot_mask = pipes.calculatePlotMask(pipes.template_img, pipes.common_size)
    flower_mask = pipes.calculateFlowerAreaMask(pipes.region_matrix, plot_bound, pipes.common_size)
    est_packs = []
    ii = 0
    for pack in packs:
        print(ii)
        if(len(pack[2].shape) !=0):
            est_packs.append( pipes.commonEstimate(pack, (plot_mask)))
        ii = ii+1

    hist_b_all = []
    all_array = est_packs
    for i, element in enumerate(all_array):
        #print(element)
        histogrm = element[2]
        hist_b_all.append(histogrm[0])

    avg_hist_b = pipes.computeAverageHistograms(hist_b_all)  # Need to convert it in array
    for pack in est_packs:
        imgs = pipes.commonModel(pack, (avg_hist_b))
        imgs = pipes.commonAnalysisTransform(imgs, (flower_mask, segm_B_lower))
        pipes.commonSave(imgs)
    processing_end_time = time() - processing_start_time
    print("SUCCESS: Images procesed in {} seconds".format(round(processing_end_time, 3)))

#127.0.0.1 akm523 523@mitm /hadoopdata/stitching /hadoopdata/stitch_result '*'
def imageStitching():
    print(sys.argv[1:8])
    server = sys.argv[1]
    uname = sys.argv[2]
    upass = sys.argv[3]
    print('From web .............')
    print(uname)
    data_path = sys.argv[4]
    save_path = sys.argv[5]
    img_type = sys.argv[6]
    pipes = ImageStitching(server, uname, upass)
    pipes.setLoadAndSavePath(data_path, save_path)
    file_bundles = collectBundle(pipes, img_type)
    rdd = loadBundle(pipes, file_bundles)
    processing_start_time = time()
    for bundle in rdd:
        pack = pipes.commonTransform(bundle, ((1280, 960)))
        pack = pipes.commonEstimate(pack, ('sift'))
        fs,img, entt = pack
        print("chechking entity")
        for ent in entt[1]:
            print(str(len(ent)))
            print(ent)
        pack = pipes.commonModel(pack, (0))
        pack = pipes.commonAnalysisTransform(pack, (0))
        pipes.write_stitch_images(pack)
    processing_end_time = time() - processing_start_time
    print("SUCCESS: Images procesed in {} seconds".format(round(processing_end_time, 3)))

def collectImgSets():
    print(sys.argv[1:8])
    server = sys.argv[1]
    uname = sys.argv[2]
    upass = sys.argv[3]
    print('From web .............')
    print(uname)
    data_path = sys.argv[4]
    save_path = sys.argv[5]
    img_type = sys.argv[6]
    pipes = ImageStitching(server, uname, upass)
    pipes.setLoadAndSavePath(data_path, save_path)
    file_lists = pipes.collectDirs(img_type)
    sets = pipes.collectImgsAsGroup(file_lists)
    print(sets)

# 127.0.0.1 akm523 523@mitm /hadoopdata/csvfile/plotsegment.csv /hadoopdata/plot_result '*' 155
def plotSegment():
    print(sys.argv[1:8])
    server = sys.argv[1]
    uname = sys.argv[2]
    upass = sys.argv[3]
    print('From web .............')
    print(uname)
    data_path = sys.argv[4]
    save_path = sys.argv[5]
    img_type = sys.argv[6]
    pipes = PlotSegment(server, uname, upass)
    pipes.setCSVAndSavePath(data_path, save_path)
    imgfile_withparams = pipes.ImgandParamFromCSV("path","param")
    for file in imgfile_withparams:
        print(imgfile_withparams[file])
    data_packs = loadFiles(pipes, list(imgfile_withparams))
    for img in data_packs:
        processed_pack = pipes.commonEstimate(img,(imgfile_withparams))
        ploted_img = pipes.commonAnalysisTransform(processed_pack,(imgfile_withparams))
        pipes.commonSave(ploted_img)

if(__name__=="__main__"):
    print(sys.argv[0:11])
    if sys.argv[1] == "registerimage":
        callImgReg()
    #callImgReg()
    #callImgSeg()
    #callFlowerCount()
    #imageStitching()
    #collectImgSets()
    # plotSegment()
