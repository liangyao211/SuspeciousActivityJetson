import os
from config_site import *
import requests
import logging

class aws_face_detector:
    def __init__(self) -> None:
        pass
    def predict(self,file_in):
        try:
            resp = requests.post(url=aws_verifyface, files=[('file',open(file_in, 'rb'))])
            data = resp.json()
            names=data['message']['names']
            boxes=data['message']['boxes']
        except:
            logging.error('Not reponse from face API')
            names=[]
            boxes=[]
        return names, boxes