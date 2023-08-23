import os
import numpy as np
from six import BytesIO
from PIL import Image
import os
from config_site import *
import requests
import logging


class aws_detector:
    def __init__(self) -> None:
        super().__init__()
        pass


    def predict(self,file_in):
        detections={'detection_boxes':[],
                    'detection_scores':[],
                    'detection_classes':[]}

        try:
            files = {'file': open(file_in, 'rb')}
            resp=requests.post(aws_get_objects, files=files)
            data = resp.json()
            res=data['message']

            for bbox,score,obj in zip(res['detection_boxes'],res['scores'],res['class_labels']):
                
                if score>0.1:
                    name=obj
                    if name=='person':
                        if score<0.5:  ## person detection need high confidence..!
                            continue
                    elif score<0.8:
                        continue

                    if name in FILTER_CLASS:
                        detections['detection_boxes'].append(bbox)
                        detections['detection_scores'].append(score)
                        detections['detection_classes'].append(name)
        except:
            logging.error('No response from object detection server')

        return [detections]