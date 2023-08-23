import requests
import json
import cv2
import logging
import boto3
from botocore.exceptions import ClientError
import os
from config_site import *
import subprocess
import random
from datetime import datetime
import s3_settings as settings
import logging
from collections import Counter
from statistics import mode

Classes=['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow']
default_dict={'detection_boxes':[],'detection_scores':[],'detection_classes':[],'ids':[]}


class ObjectTracker:
    def __init__(self,det_fps):
        self.history=[default_dict]*int(det_fps)
        self.isup_hist=[False]*int(det_fps)
        self.n_objects=0
        print(f'Object tracking histroy of {det_fps} frames')
        
    def update_objects(self, detections,isup):
        self.history.append(detections)
        self.isup_hist.append(isup)
        self.object_count=dict(zip(Classes,[[]]*len(Classes)))
        confs=[]
        dists=[]
        is_suspicious=[]
        ids=[]

        for d in self.history:
            dict_count=Counter(d['detection_classes'])
            confs.extend(d['detection_scores'])
            dists.append(min(d.get('dist',[-1])))
            if 'ids' in d:
                ids.extend(d['ids'])
            else:
                ids.append("NA")

            for obj,count in self.object_count.items():
                ll=self.object_count[obj].copy()
                if obj in dict_count:
                     ll.append(dict_count[obj])
                else:
                    ll.append(0)
                self.object_count[obj]=ll
        
        self.ids=set(ids)

        self.final_count={}

        for obj,counts in self.object_count.items():
            mode_count=mode(counts)
            if mode_count>0:
                 self.final_count[obj]=mode_count

        
        self.n_objects=sum(self.final_count.values())
        self.desc=''
       # print(self.object_count)
       


        if self.n_objects>0:
            self.conf=max(confs)
            self.min_dist=min([d for d in dists if d>=0])
            self.is_suspicious=sum(self.isup_hist)>round(0.2*len(self.isup_hist))

            max_count=0
            for obj,count in self.final_count.items():
                self.desc+=f'{count} {obj}(s) found,'
                if count>max_count:
                    self.label=obj
                    max_count=count
        else:
            self.min_dist=-1
            self.desc='No objects found'


        self.history=self.history[1:]
        self.isup_hist=self.isup_hist[1:]


class FileDb:
    def __init__(self,filepath, entries):
        self.entries_susp=sa_dict.keys()
        self.entries_face=face_log_dict.keys()
        self.file='./dump_dir/databse.csv'
        self.file_db = open(self.file,'a')
        self.file_db.write('\n')

    
    def write_to_db(self,sdict):
        line=''
        if 'subject' in sdict:
            entries=self.entries_face
        else:
            entries=self.entries_susp

        for e in entries:
            line+=str(sdict[e])+'#'
        self.file_db = open(self.file,'a')
        self.file_db.write(line)
        self.file_db.write('\n')
        self.file_db.close()
        #print(f'Written line {line}')


def put_REST(api_url,variables,file_db=None):

    if ENABLE_REPORTING:
        print(json.dumps(variables))
        response = requests.post(api_url, data=json.dumps(variables), headers=headers)
        print(response.json())
        return response.json(), response.status_code
    else:
        if api_url==incident_api:
            response={}
            response['id']=0
            return response, 201
        else:
            print(json.dumps(variables))
            variables['created_on']=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            file_db.write_to_db(variables)
            return 0,0
        


def generate_nonce(length=8):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


class CabinIncidentReporter:
    def __init__(self,video_name):
        self.file_db=None
        if not ENABLE_REPORTING:
            self.file_db = FileDb('./dump_dir/databse.csv',['created_on','label','camera','description','confidence','distance','is_suspicious','media','incident','id'])

        out_incident,status=put_REST(incident_api,incident_dict,self.file_db)
        self.incident_id=out_incident["id"]
        
        self.s3_path=f'camera-feeds/site/{incident_dict["site"]}/camera/{sa_dict["camera"]}/incident/{self.incident_id}/suspact'
        self.video_name=video_name
        self.filename=self.video_name.split('/')[-1][:-4]
        
        self.filename_org=self.filename+'.mp4' if upload_mp4 else self.video_name[-4:]
        self.s3_name=self.filename+'.mp4'

        logging.debug(f'Reporitng a main incident in {self.filename} using incident Id {self.incident_id}')


    def report_face_incident(self, names):
        ids=names
        send_dict=face_log_dict.copy()
        send_dict["incident"]=self.incident_id
        send_dict["media"]=self.s3_name
        send_dict["confidence"]=0.8  ### Update it..!\

        if '<unknown>' in ids:
            send_dict["subject"]='<unknown>'
            #send_dict["personale"]='<unknown>'
        else:
            send_dict['authorised']=True
            send_dict["subject"]=ids[0]
            #send_dict["personale"]=int(send_dict["personale"])
        out,status=put_REST(log_face_reco,send_dict,self.file_db) 
        return status
    
    def upload_video(self):
        print(f'uploading {self.video_name}')
        status=self.upload_file(self.video_name,BUCKET)
        print('upload complete')        

    def upload_file(self,file_name, bucket):
        object_name = self.s3_name
        # Upload the file
        s3_client = boto3.client('s3', aws_access_key_id=settings.aws_access_key_id,
                                       aws_secret_access_key=settings.aws_secret_access_key,
                                       region_name=settings.region_name)
        try:
            print(f'uploading to {self.s3_path}/{object_name}')
            response = s3_client.upload_file(file_name, bucket, f'{self.s3_path}/{object_name}')
            os.remove(file_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True
    

class IncidentReporter:
    def __init__(self,video_name):
        self.file_db=None
        if not ENABLE_REPORTING:
            self.file_db = FileDb('./dump_dir/databse.csv',['created_on','label','camera','description','confidence','distance','is_suspicious','media','incident','id'])

        out_incident,status=put_REST(incident_api,incident_dict,self.file_db)
        self.incident_id=out_incident["id"]
        
        self.s3_path=f'camera-feeds/site/{incident_dict["site"]}/camera/{face_log_dict["camera"]}/incident/{self.incident_id}/suspact'
        self.video_name=video_name
        self.filename=self.video_name.split('/')[-1][:-4]
        
        self.filename_org=self.filename+'.mp4' if upload_mp4 else self.video_name[-4:]
        self.s3_name=self.filename+'.mp4'

        logging.debug(f'Reporitng an cabin incident in {self.filename} using incident Id {self.incident_id}')

        self.obj_tracker=ObjectTracker(int(1.0/OBJ_UPDATE_FREQ))
        self.log_update_counter=0
        self.UPDATE_COUNT=LOG_UPDATE_FREQ*FPS_VIDEO
        self.last_log=None
    
    def update_objects(self,results):
        dets=results['detection_result'][0]
        self.obj_tracker.update_objects(dets,results["SA"])

    def report_incident(self,results):
        send_dict=sa_dict.copy()
        send_dict["incident"]=self.incident_id
        send_dict["media"]=self.s3_name

        if  self.obj_tracker.n_objects>0:
            
            send_dict["label"]=self.obj_tracker.label

            if self.obj_tracker.min_dist==999:
                self.obj_tracker.min_dist=-1
        
            send_dict["distance"]=round(self.obj_tracker.min_dist,2)
        
            
            send_dict["confidence"]=round(self.obj_tracker.conf,2)
            send_dict["is_suspicious"]=self.obj_tracker.is_suspicious
            send_dict["media"]=self.s3_name

            send_dict["description"]=self.obj_tracker.desc
            #print(send_dict)

            if self.last_log is None or self.is_log_different(send_dict):
                out,status=put_REST(log_sus_activity,send_dict,self.file_db)
            
            self.last_log=send_dict

    def is_log_different(self, cur_log):
        for k,v in cur_log.items():
            if k!='distance' and k!='id' and k!='confidence':
                if v!=self.last_log[k]:
                    return True
        return False
    
    def upload_video(self):
        print(f'uploading cabin video {self.video_name}')
        status=self.upload_file(self.video_name,BUCKET)
        print('upload complete')        

    def upload_file(self,file_name, bucket):
        object_name = self.s3_name
        # Upload the file
        s3_client = boto3.client('s3', aws_access_key_id=settings.aws_access_key_id,
                                       aws_secret_access_key=settings.aws_secret_access_key,
                                       region_name=settings.region_name)
        try:
            print(f'uploading to {self.s3_path}/{object_name}')
            response = s3_client.upload_file(file_name, bucket, f'{self.s3_path}/{object_name}')
            os.remove(file_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True