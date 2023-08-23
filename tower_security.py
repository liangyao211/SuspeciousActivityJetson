import os
from utils import ConfigDict, JsonifyResult
import gc
import cv2
import numpy as np
from datetime import datetime
import logging
from face_detection import aws_face_detector
from object_detection import aws_detector
from fence_detection import aws_segmentor
import logging
CV2_VERSION=cv2.__version__

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def GetContours(mask):
    w,h=mask.shape
    mask_in=(mask*255.0).astype(np.uint8)
    kernel = np.ones((3, 3), np.uint8)
    mask_post = cv2.erode(mask_in,kernel,iterations = 1)

    per=3
    kernel = np.ones((round(per*h/100), (round(per*w/100))), np.uint8)
    mask_post = cv2.dilate(mask_post, kernel, iterations=1)
    mask_post_edge = cv2.Canny(mask_post, 75, 200)
    if CV2_VERSION=='4.8.0' or CV2_VERSION=='4.1.2':
        contours, _= cv2.findContours(mask_post_edge,cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    else:
        _,contours, hierarchy= cv2.findContours(mask_post_edge,cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    return contours, mask_post

def GetSuspIntrutionAreas(mask):
    ######## Fence contour computation ###########
    w,h=mask.shape
    contours, mask_post=GetContours(mask)

    ######## Intrution area detection #################
    mask_intu=np.zeros(mask.shape,dtype=np.uint8)

    no_points=0

    for cnt in contours:
        for points in cnt:
            pt=points[0]
            mask_intu[pt[1]+1:,pt[0]]=255
            no_points+=1

    mask_intu=mask_intu-mask_post
    
    contours_intrution, _=GetContours(mask_intu>128)

    return mask_post>128,mask_intu>128, contours, contours_intrution


class TowerSecurity:

    def __init__(self, w=2304 , h=1296) -> None:
        self.segmentor=aws_segmentor()
        self.detector=aws_detector()
        self.face_recog=aws_face_detector()

        self.mask=0.0
        self.Last_mask_update_time=None
        self.fence_update_rate = 0 #float(config.segmentor['update_rate'])
        self.min_fence_percent= 1.0 
        self.w=w
        self.h=h

    def UpdateMask(self,cur_mask):
        if np.sum(self.mask)>0:
            if np.sum(cur_mask)<round(0.1*self.w*self.h/100):
                logging.critical('The mask seems to be not detected..! Using last known mask..!')
            else:
                self.mask=cur_mask #(1-self.alpha)*cur_mask+self.alpha*self.mask
                self.mask=(self.mask>0.5).astype(np.float32)
                self.mask,self.mask_intu, self.contours, self.contours_intrution=GetSuspIntrutionAreas(self.mask)
                logging.critical('Mask updated..!')     
        else:
            print(bcolors.WARNING +'Updating first masks now..!'+ bcolors.ENDC)
            self.mask=cur_mask
            self.w,self.h=self.mask.shape
            self.mask,self.mask_intu, self.contours, self.contours_intrution=GetSuspIntrutionAreas(self.mask)
            logging.critical('Mask updated..!')  



    def computeDistance(self,x,y):
        #print(x,y)
        if x<self.mask_intu.shape[0] and y<self.mask_intu.shape[1]:
            if self.mask_intu[x,y]:
                dist=0
            else:
                dists = [cv2.pointPolygonTest(cnt, (round(y),round(x)), True) for cnt in self.contours]
                dist=np.sqrt(-min(dists))
            is_intru=self.mask_intu[x,y]
            is_sup=self.mask[x,y]
        else:
            logging.error('This is not correct, not sure why its happening..!')
            dists = [cv2.pointPolygonTest(cnt, (round(y),round(x)), True) for cnt in self.contours]
            dist=np.sqrt(-min(dists))
            is_intru=False
            is_sup=False

        return dist*10.0, is_intru, is_sup

    def update_fence_mask(self, image):
        try:
            if self.Last_mask_update_time is None:
                _, cur_masks=self.segmentor.predict(image)
                self.UpdateMask(cur_masks)
                self.Last_mask_update_time=datetime.now()
            else:
                diff=(datetime.now()-self.Last_mask_update_time).total_seconds() / 60.0
                if diff>self.fence_update_rate or self.mask is None:
                    print(bcolors.WARNING +'Updating the masks..!  Might take a while..!'+ bcolors.ENDC)
                    _, cur_masks=self.segmentor.predict(image)
                    self.UpdateMask(cur_masks)
        except Exception as e:
            print(e)
            print(bcolors.WARNING +'No reponse from server..!'+ bcolors.ENDC)


    def Monitor(self, images_obj_det, format_result=False):
        detections=self.detector.predict(images_obj_det)
        #self.update_fence_mask(images_fence_det)
        suspecious_activity=False
        Intrution = False

        if len(detections[0]['detection_boxes'])>0:
            detections=self.ComputeFence2ObjectDistance(detections, images_obj_det)

            suspecious_activity=self.DetectSuspciousActivity(detections)

            Intrution= self.DetectIntrution(detections)
            

        result={'SA': suspecious_activity, 'Intrution': Intrution,  'detection_result': detections}
        return JsonifyResult(result)

    def DetectIntrution(self,detections):
        ### Write the Suspicious activity detector based on distance here..!
        for d in detections:
            for onf in d['in_side_fence']:
                if onf:
                    return True
        return False

    def DetectSuspciousActivity(self,detections):
        ### Write the Suspicious activity detector based on distance here..!
        for d in detections:
            for onf in d['on_fence']:
                if onf:
                    return True
        return False

    def ComputeFence2ObjectDistance(self, detections,images_obj_det):

        for idx,d in enumerate(detections):
            dist=[]
            inside_fence=[]
            on_fence=[]
            ids=[]
            for bbox,obj in zip(d['detection_boxes'],d['detection_classes']):
                ymin, xmin, ymax, xmax=round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3])
                #ref_point=np.array([(xmin+xmax)//2,ymax])
                ref_point=np.array([xmin,ymin])
                #print('debug_info',self.h,self.w,ymax,ymin,bbox)            
                # try:
                dist_d, ins_fe, on_fe=self.computeDistance(ref_point[0],ref_point[1])
                # if ins_fe or on_fe:
                #     if obj=='person':
                #         cur_id=self.face_recog.predict(cv2.imread(images_obj_det),[ymin, xmin, ymax, xmax])
                #         ids.append(cur_id)
                # else:
                #     ids.append("NA")

                dist.append(float(dist_d))
                inside_fence.append(float(ins_fe))
                on_fence.append(float(on_fe))
            detections[idx]['dist']=dist
            detections[idx]['in_side_fence']=inside_fence
            detections[idx]['on_fence']=on_fence
            # detections[idx]['ids']=ids

        return detections

    def VerifyFaces(self, image):
        names, boxes=self.face_recog.predict(image)
        return names, boxes
