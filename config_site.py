SITE_ID=7

BUCKET='shurikonekt-media'
REQ_EXT='m4v'
#REQ_EXT='mkv'
FPS_VIDEO=60
upload_mp4=False
proc_fps=0.2
hide_name=True
ENABLE_REPORTING=True
VISUALIZE=True

VIS_MATHOD='DIRECT'  ## DIRECT --> stores the video directly (fast), INDIRECT--> Stores images and makes videos (slow)

FILTER_CLASS=['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow']

LOG_UPDATE_FREQ=0.1 ##In seconds
MASK_UPDATE_FREQ=20*60
OBJ_UPDATE_FREQ=0.1
FACE_UPDATE_FREQ=2.0


incident_api='http://shuri-edge-microservice-1496798465.eu-west-1.elb.amazonaws.com:8000/api/operations/incident'

log_face_reco='http://shuri-edge-microservice-1496798465.eu-west-1.elb.amazonaws.com:8000/api/operations/log-facial-recognition'

log_sus_activity='http://shuri-edge-microservice-1496798465.eu-west-1.elb.amazonaws.com:8000/api/operations/log-suspicious-activity'

#aws_endpoint='https://3eab-2406-7400-51-542c-b4c9-7ca7-6f32-1f8a.ngrok-free.app'

#aws_endpoint='http://localhost:8081' #https://681a-106-51-167-201.ngrok-free.app
#aws_endpoint='http://ec2-52-31-150-156.eu-west-1.compute.amazonaws.com:8081'
aws_endpoint='http://ec2-52-31-150-156.eu-west-1.compute.amazonaws.com:8081'

#aws_endpoint='https://9c4e-106-51-167-201.ngrok-free.app'
#aws_endpoint='http://ubuntu@ec2-34-245-235-235.eu-west-1.compute.amazonaws.com:8081'

aws_get_objects=f'{aws_endpoint}/get_objects_asone_yolo'

aws_get_fence=f'{aws_endpoint}/get_fence'

aws_verifyface='http://face-api-1231261094.eu-west-1.elb.amazonaws.com/verify_faces'


headers =  {"Content-Type":"application/json"}

incident_dict={"site": "7"}

face_log_dict={
    "authorised": False,
    "media": 'Link to file',
    "subject": "<unknwn>",
    "confidence": 0.3,
    "camera": "E8ABFAA7BEC9",
    "personale": 3,
    "incident": "No"
}

sa_dict={
    "label": "No object detected",
    "camera": "E8ABFAA7BEC9",
    "description": "No Persons Detected",
    "confidence": 1.0,
    "distance": -1,
    "is_suspicious": False,
    "media": "Random_URL",
    "incident": 51,
    "id": "51"
}

Stream_main='rtsp://nvr:foscam123@192.168.88.111:8011/videoMain'
Stream_cabin='rtsp://nvr:foscam123@192.168.88.111:8011/videoMain'
