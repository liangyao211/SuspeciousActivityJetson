
import imutils
import cv2
import logging


class MotionDetector:
    def __init__(self, name) -> None:
        self.name=name
        self.FRAMES_TO_PERSIST = 10
        self.MIN_SIZE_FOR_MOVEMENT = 300
        self.MOVEMENT_DETECTED_PERSISTENCE = 100
        self.first_frame=None
        self.next_frame = None
        self.delay_counter = 0
        self.movement_persistent_counter = 0


    def detect_motion(self, frame):
        transient_movement_flag = False
        frame = imutils.resize(frame, width = 1024)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.first_frame is None: self.first_frame = gray

        self.delay_counter += 1

        # Otherwise, set the first frame to compare as the previous frame
        # But only if the counter reaches the appriopriate value
        # The delay is to allow relatively slow motions to be counted as large
        # motions if they're spread out far enough
        if self.delay_counter > self.FRAMES_TO_PERSIST:
            self.delay_counter = 0
            self.first_frame = self.next_frame
        
        self.next_frame = gray
        frame_delta = cv2.absdiff( self.first_frame, self.next_frame)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        # Fill in holes via dilate(), and find contours of the thesholds
        thresh = cv2.dilate(thresh, None, iterations = 2)
        try:
             _,cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        except:
            cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
           
        for c in cnts:

            # Save the coordinates of all found contours
            (x, y, w, h) = cv2.boundingRect(c)
            
            # If the contour is too small, ignore it, otherwise, there's transient
            # movement
            if cv2.contourArea(c) > self.MIN_SIZE_FOR_MOVEMENT:
                transient_movement_flag = True
                
                # Draw a rectangle around big enough movements
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if transient_movement_flag == True:
            # logging.debug(f'Mumentary motion detected in {self.name}')
            self.movement_persistent_flag = True
            self.movement_persistent_counter = self.MOVEMENT_DETECTED_PERSISTENCE

        # As long as there was a recent transient movement, say a movement
        # was detected    
        if self.movement_persistent_counter > 0:
            # logging.debug(f'Motion detected in {self.name}')
            detected=True
            self.movement_persistent_counter -= 1
        else:
            detected=False

        return detected, frame







        