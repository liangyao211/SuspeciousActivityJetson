import cv2

vcap = cv2.VideoCapture('rtsp://nvr:foscam123@192.168.88.111:8011/videoMain')

inds=0

while(1):

    ret, frame = vcap.read()
    print(ret)
    cv2.imwrite(f'save_image_{inds}_main.jpg',frame)
    break

vcap = cv2.VideoCapture('rtsp://nvr:foscam123@192.168.88.110:8010/videoMain')

inds=0

while(1):

    ret, frame = vcap.read()
    print(ret)
    cv2.imwrite(f'save_image_{inds}_cabin.jpg',frame)
    break

