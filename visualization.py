import cv2
import numpy as np
import os
import statistics
from config_site import *

class Visualization:
    def __init__(self, vid_name, detection=True, draw_mask=False, resolution=(1280,720)): ##Change it
        self.video=vid_name
        self.vid_name=vid_name[:-4]

        if VIS_MATHOD=='INDIRECT':
            os.mkdir(self.vid_name)
        else:
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            self.out_video = cv2.VideoWriter(vid_name[:-4]+'.mp4', fourcc, FPS_VIDEO, resolution)
        self.resolution=resolution

        self.draw_mask=draw_mask
        self.detection=detection

        self.count=0
        self.count_history=[0]*4

        

    def med_filt(self,cur_count):
        self.count_history.append(cur_count)
        count=statistics.median(self.count_history)
        self.count_history=self.count_history[1:]
        return count


    def WriteFrame(self,image, d=None, mask_intru=None, mask_fence=None, n_objects=None):
        w,h,_=image.shape
        im_fill=image
        if self.detection:
            ## Write the fence and intution areas..!
            
            if self.draw_mask:
                im_fill[:,:,2]=0.5*255*mask_fence+0.5*image[:,:,2]
                im_fill[:,:,0]=0.5*255*mask_intru+0.5*image[:,:,0]
                im_fill=im_fill.astype(np.uint8)

            cv2.putText(im_fill,f'{n_objects} objects found',(round(image.shape[1]*0.8),round(image.shape[0]*0.9)),0,1.5,(0,0,255),2)
            if len(d['detection_boxes'])>0:
                ## Write the bouding boxes..!
                for bbox, det_obj, dist, on_fence, in_fence, conf in zip(d['detection_boxes'],d['detection_classes'],d['dist'],d['on_fence'],d['in_side_fence'],d['detection_scores']):
                    xmin, ymin, xmax, ymax=round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3])
                    if in_fence:
                        clr=(255,255,0)  #BGR
                    elif on_fence:
                        clr=(0,0,255)
                    else:
                        clr=(0,255,0)

                    cv2.rectangle(im_fill,(xmin,ymin),(xmax,ymax),clr,2)
                    cv2.putText(im_fill,det_obj+':'+"{:.1f}".format(dist/max([h,w]))+','+"{:.2f}".format(conf)+':',(xmax+10,ymax),0,1.0,(0,0,255),2)

        if VIS_MATHOD=='INDIRECT':
            cv2.imwrite(self.vid_name+"/{:04d}".format(self.count)+'.bmp',im_fill)
        else:
            self.out_video.write(cv2.resize(image.astype(np.uint8), self.resolution))
        self.count+=1

    def release(self):
        print(f'viz video is written to {self.video}')
        
        if VIS_MATHOD=='INDIRECT':
            print('ffmpeg -y -framerate 30 -i '+self.vid_name+'/%4d.bmp -c:v libx264 '+self.video)
            os.system('ffmpeg -y -framerate 30 -i '+self.vid_name+'/%4d.bmp -c:v libx264 '+self.video)
            os.system(f'rm -rf {self.vid_name}')
        else:
            self.out_video.release()

       
class Visualization_face:
    def __init__(self, vid_name, detection=True, draw_mask=False, resolution=(1280,720)): ##Change it (1280,720)
        self.video=vid_name
        self.vid_name=vid_name[:-4]
        self.resolution=resolution
        if VIS_MATHOD=='INDIRECT':
            os.mkdir(self.vid_name)
        else:
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            self.out_video = cv2.VideoWriter(vid_name[:-4]+'.mp4', fourcc, FPS_VIDEO, resolution)
            
        self.count=0

    def WriteFrame(self,image, names, boxes):
        if len(names)>0:
            for box,name in zip(boxes,names):
                box=[int(bb) for bb in box]
                cv2.rectangle(image,(box[0],box[1]),(box[2],box[3]), (255, 0, 0), 2)
                cv2.putText(image,name, (int(box[0]),int(box[1])-30),0,1.0,(255,0,0,255),2) #+':'+"%.2f" % fp

        if VIS_MATHOD=='INDIRECT':
            cv2.imwrite(self.vid_name+"/{:04d}".format(self.count)+'.bmp',image)
        else:
            self.out_video.write(cv2.resize(image.astype(np.uint8), self.resolution))
        self.count+=1

    def release(self):
        print(f'viz video is written to {self.video}')
        if VIS_MATHOD=='INDIRECT':
            print('ffmpeg -y -framerate 30 -i '+self.vid_name+'/%4d.bmp -c:v libx264 '+self.video)
            os.system('ffmpeg -y -framerate 30 -i '+self.vid_name+'/%4d.bmp -c:v libx264 '+self.video)
            os.system(f'rm -rf {self.vid_name}')
        else:
            self.out_video.release()

