import  cv2
input_video='dump_dir/test_videos/test5_small.m4v'
output_rtsp_url = "https://sampath-usea.streaming.media.azure.netmanifest.ism/manifest(format=m3u8-cmaf)"

cap = cv2.VideoCapture(input_video)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
output_stream = cv2.VideoWriter(output_rtsp_url,  cv2.CAP_FFMPEG,  0,  fps,  (width,  height))
while  True:
    ret,  frame = cap.read()
    if  not  ret:
        cap = cv2.VideoCapture(input_video)
        print('opening new video')
        continue;
    
    output_stream.write(frame)
    cv2.imshow("Processed Frame",  frame)
    if  cv2.waitKey(1) == ord("q"):
        break

cap.release()

output_stream.release()

cv2.destroyAllWindows()