import cv2

vcap1 = cv2.VideoCapture('rtsp://nvr:foscam123@192.168.88.111:8011/videoMain')
vcap2 = cv2.VideoCapture('rtsp://nvr:foscam123@192.168.88.110:8010/videoMain')
frame_no=0


fourcc = cv2.VideoWriter_fourcc(*'MP4V')
out1 = cv2.VideoWriter('output_main.mp4', fourcc, 20.0, (2304,1296))
out2 = cv2.VideoWriter('output_cabin.mp4', fourcc, 20.0, (1280,720))

while(1):
    frame_no+=1
    ret1, frame1 = vcap1.read()
    ret2, frame2 = vcap2.read()
    if ret1:
        out1.write(frame1)
    if ret2:
        out2.write(frame2)
    print(f'Frame: {frame_no}')
    c = cv2.waitKey(1)
    if c & 0xFF == ord('q'):
        break

vcap1.release()
vcap2.release()
out1.release()
out2.release()



