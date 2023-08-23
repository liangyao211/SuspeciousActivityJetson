from utils import read_config
from tower_security import TowerSecurity

from logger import IncidentReporter, CabinIncidentReporter
from video_utils import Video2Frame, m4v_reader
from config_site import *
import cv2
import numpy as np
#from werkzeug import secure_filename
from visualization import Visualization, Visualization_face
from fence_detection import mask2rle
import glob
import os
import time
from camera import MotionDetector
import logging
import uuid
import sys
import imutils

LOG_UPDATE_IMAGES=LOG_UPDATE_FREQ*FPS_VIDEO
MASK_UPDATE_IMAGES=MASK_UPDATE_FREQ*FPS_VIDEO
OBJ_UPDATE_IMAGES=round(OBJ_UPDATE_FREQ*FPS_VIDEO)
FACE_UPDATE_IMAGES=round(FACE_UPDATE_FREQ*FPS_VIDEO)

class FrameProcessor:
    def __init__(self, ) -> None:
        self.security=TowerSecurity()
        self.vid1=None
        self.vid2=None
        self.detector1=MotionDetector('Main Camera')
        self.detector2=MotionDetector('Cabin Camera')
        self.mask_update_counter=MASK_UPDATE_IMAGES
        self.count=0
        self.avg_proc_time=0.0
        self.last_mot1=False
        self.last_mot2=False
        #self.start_new_video()

    def start_cabin_video(self):
        logging.debug('Starting the cabin video')
        self.face_update_counter=FACE_UPDATE_IMAGES
        self.vid_name=str(uuid.uuid4())
        self.face_reporter=CabinIncidentReporter('./dump_dir/'+self.vid_name+'_cabin.mp4')
        self.viz_cabin=Visualization_face('./dump_dir/'+self.vid_name+'_cabin.mp4')

    def end_cabin_video(self):
        logging.debug('Ending cabin video')
        if VISUALIZE:
            self.viz_cabin.release()

        #vidcap.destroy()
        if ENABLE_REPORTING:
            self.face_reporter.upload_video()


    def start_main_video(self):
        logging.debug('Starting the new video')

        self.all_dets={}
        self.log_update_counter=0
        self.obj_update_counter=OBJ_UPDATE_IMAGES
        
        self.avg_proc_time=0
        self.atleast_one_report=False
        self.vid_name=str(uuid.uuid4())
        self.reporter=IncidentReporter('./dump_dir/'+self.vid_name+'_main.mp4')

        self.viz=Visualization('./dump_dir/'+self.vid_name+'_main.mp4')

    def end_main_video(self):
        logging.debug('Ending the video')
        # if (not  self.atleast_one_report) and ENABLE_REPORTING:
        #     self.reporter.report_incident(final_out)

        if VISUALIZE:
           self.viz.release()
        #vidcap.destroy()
        if ENABLE_REPORTING:
            self.reporter.upload_video()

    def mask_detection(self, image):
        if self.mask_update_counter>=MASK_UPDATE_IMAGES:
            try:
                start=time.time()
                image_path='./dump_dir/cur_image_main_cam.jpg'
                cv2.imwrite(image_path, image)
                self.security.update_fence_mask(image_path)
                logging.debug(f'Mask detection took {time.time()-start}')
                self.mask_update_counter=0
            except Exception as e:
                    print('Failed to obtain the fenace mask, We try next iteration..!: '+ str(e))
        self.mask_update_counter+=1

    def object_detection(self, image):
        if self.obj_update_counter>=OBJ_UPDATE_IMAGES:
            start=time.time()
            image_path='./dump_dir/cur_image_main_cam.jpg'
            cv2.imwrite(image_path, image)
            self.final_out=self.security.Monitor(image_path, format_result=False)
            self.det_results=self.final_out['detection_result'][0]
            self.reporter.update_objects(self.final_out)
            logging.debug(f'object detection took {time.time()-start}')
            self.obj_update_counter=0
        self.obj_update_counter+=1


    def face_detection(self, image):
        if self.face_update_counter>=FACE_UPDATE_IMAGES:
            start=time.time()
            image_path='./dump_dir/cur_image_main_cam.jpg'
            cv2.imwrite(image_path, image)
            self.names, self.boxes=self.security.VerifyFaces(image_path)
            if len(self.names)>0:
                self.face_reporter.report_face_incident(self.names)
            logging.debug(f'Face detection took {time.time()-start}')
            self.face_update_counter=0
        self.face_update_counter+=1


    def report_incident(self):
        if (self.reporter.obj_tracker.n_objects)>0 and self.log_update_counter>=LOG_UPDATE_IMAGES:
            start=time.time()
            self.reporter.report_incident(self.final_out)
            self.atleast_one_report=True
            self.log_update_counter=0
            logging.debug(f'incident reporting took {time.time()-start}')
        self.log_update_counter+=1

    def motion_detection(self, image1, image2):
         det1=self.detector1.detect_motion(image1)
         det2=self.detector1.detect_motion(image2)
         return det1, det2

    def process_frame(self, image1=None, image2=None):
        self.count+=1
        start_time=time.time()
        mot1, mot2= False, False

        if image1 is not None:
            mot1, _=self.detector1.detect_motion(image1)
            if (not mot1) or (self.security.Last_mask_update_time is None):
                self.mask_detection(image1)

        if image2 is not None:
            mot2, _=self.detector2.detect_motion(image2)

        if (not self.last_mot1) and mot1:
            self.start_main_video()

        if (not self.last_mot2) and mot2:
            self.start_cabin_video()

        if mot1:
            logging.debug(' Motion detected in Main camera')
            self.object_detection(image1)
            self.report_incident()

            if VISUALIZE:
                #print('writing the visualization')
                start=time.time()
                self.viz.WriteFrame(image1,self.det_results, self.security.mask_intu, self.security.mask, self.reporter.obj_tracker.n_objects)
                logging.debug(f'Writing main viz took {time.time()-start}')
                #self.all_dets[str(fidx)]=det_results

        if mot2:
            logging.debug(' Motion detected in Cabin camera')
            self.face_detection(image2)
            if VISUALIZE:
                start=time.time()
                self.viz_cabin.WriteFrame(image2,self.names,self.boxes)
                logging.debug(f'Writing cabin viz took {time.time()-start}')
            
        self.avg_proc_time+=time.time()-start_time
        if  self.count==100:
            fps=100/ self.avg_proc_time
            logging.info('processing fps: {fps}')
            self.count=0
            self.avg_proc_time=0

        if self.last_mot1 and (not mot1):
            self.end_main_video()
        
        if self.last_mot2 and (not mot2):
            self.end_cabin_video()
        
        self.last_mot1=mot1
        self.last_mot2=mot2

    def process_video_stream(self, stream_main, stream_cabin):
        if self.vid1==None:
            self.vid1 = cv2.VideoCapture(stream_main)

        if self.vid2==None:
            self.vid2 = cv2.VideoCapture(stream_cabin)
        fno=0.0
        while(1):
            ret_main, frame_main = self.vid1.read()
            ret_cabin, frame_cabin = self.vid2.read()
            fno+=1
            if not ret_main and not ret_cabin:
                logging.error('Not able to read both cameras')
                time.sleep(5)

            if not ret_main:
                 logging.error('Not able to read main camera')
                 print(fno)

            if not ret_cabin:
                 logging.error('Not able to cabin camera')
        
            self.process_frame(frame_main if ret_main else None, frame_cabin if ret_cabin else None)
            


if __name__ == "__main__":
    logging.basicConfig(filename='./dump_dir/run_log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    proc=FrameProcessor()

    if sys.argv[1]=='test':
        print('Using test streams')
        proc.process_video_stream('dump_dir/test_videos/test4.m4v', 'dump_dir/test_videos/test4.m4v')

    else:
        print('Using camera streams')
        proc.process_video_stream(Stream_main, Stream_cabin)


     
