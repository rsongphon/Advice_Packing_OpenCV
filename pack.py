import cv2
import numpy as np
import os
import time
import sys


month = {1:'JAN',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

def main():
    currentTime = getCurrentTime()

    # Check for folder in the system
    # Folder Structure Video/(Month)
   
    parentDir = os.getcwd()
    videoDir = os.path.join(parentDir,'Videos')
    currentMontVdo = os.path.join(videoDir,currentTime['monthName'])

    if not os.path.exists(videoDir):
        os.makedirs(videoDir)
    if not os.path.exists(currentMontVdo):
        os.makedirs(currentMontVdo)
    
    # Check the folder of video that last more than 1 month
    # recording status
    startRecord = False

    while True:
        #recordingVdo(filename = 'test1.avi')

        qrRead = {'staff':'11100215XF','order':'DSGA45D'}

        #editVideo(fileInput='rawfootage.avi',id=qrRead,time=currentTime)

        vidData = getDurationFPS(fileInput='rawfootage.avi')

        cutVideo(fileInput='rawfootage.avi',videoData=vidData,durTarget=180,mode='cut')

        exit = input("Exit(y/n)")
        print(exit.upper())
        if exit.upper() == 'Y':
            break
    
    sys.exit()

def getCurrentTime():
    currentTime = {}
    t = list(time.localtime())
    currentTime['year'] = t[0]
    currentTime['month'] = t[1]
    currentTime['monthName'] = month[t[1]]
    currentTime['day'] = t[2]
    currentTime['hour'] = t[3]
    currentTime['min'] = t[4]
    return currentTime

def recordingVdo(filename='output.avi'):
    # Start Capture raw footage
    capture = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only
    width = int(capture.get(3))
    height = int(capture.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    framerate = 17 # Framerate must be matach with the camera. See specification !!
    
    
    # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    output = cv2.VideoWriter(filename,fourcc,framerate,(width,height))
    while True:
        isTrue, frame = capture.read()
        output.write(frame)
        cv2.imshow('frame',frame)

        # read QR code or push button to break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    capture.release()
    output.release()
    cv2.destroyAllWindows()

def editVideo(fileInput,id,time):
    # Start Capture raw footage
    capture = cv2.VideoCapture(fileInput) 
    width = int(capture.get(3))
    height = int(capture.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Define the codec and create VideoWriter 
    framerate = 17 # Same as original video
    output = cv2.VideoWriter('edit.avi',fourcc,framerate, (width,height))
    
    #Reading one frame and move pointer to the next frame
    ret, frame = capture.read() # start reading

    while ret: # ret return True if the frame reading is success. 

        # Put the text in image 
        font = cv2.FONT_HERSHEY_SIMPLEX
        textLocation_staff = (0,frame.shape[0]-10)  # adjust the minus value to move the row
        textLocation_order = (0,frame.shape[0]-50)  # adjust the minus value to move the row

        cv2.putText(img = frame,text='Staff ID: '+id['staff'],org=textLocation_staff, 
                    fontFace=font, fontScale=1, color=(255, 50, 255), thickness=1, lineType =cv2.LINE_AA)

        cv2.putText(img = frame,text='Order No: '+id['order'],org=textLocation_order,
                    fontFace=font, fontScale=1, color=(255, 50, 255), thickness= 1, lineType=cv2.LINE_AA)

        output.write(frame)
        ret, frame = capture.read() # next frame

    
    capture.release()
    output.release()

def getDurationFPS(fileInput):
    capture = cv2.VideoCapture(fileInput)
    fps = capture.get(cv2.CAP_PROP_FPS)      
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps

    videoData = {'fps':fps , 'frameCount' : frame_count , 'durationSec': duration}

    print('fps = ' + str(fps))
    print('number of frames = ' + str(frame_count))
    print('duration (S) = ' + str(duration))
    minutes = int(duration/60)
    seconds = duration%60
    print('duration (M:S) = ' + str(minutes) + ':' + str(seconds))

    capture.release()

    return videoData

def cutVideo(fileInput,videoData,durTarget,mode='cut'):
    # Choose Between 2 mode 
    # 'cut' for cuting the footage into last desire duration
    # 'timeLapse' for speed up the video in desire duration

    if mode=='cut':
        # if duration more than we want (durTarget)

        # !!Count in second!!

        # cut the last footage to the value we want
        # duration = frame_count/fps >>>> frame_count = fps*duration
        fps = 17 # <<<<<!!!! adjust this value depend on the camera
        numFrameExpect = fps * durTarget

        if videoData['durationSec'] > durTarget:
            print('Video lenght is {} minute . More than {} minute'.format(str(int(videoData['durationSec']/60)),str(int(durTarget/60))))
            # Subtract actual video frame with expect frame to get checkpoint of the starting frame (last batch of the video)
            startPoint = videoData['frameCount'] - numFrameExpect
            #print(startPoint)

            # Start Capture reading video
            capture = cv2.VideoCapture(fileInput) 
            width = int(capture.get(3))
            height = int(capture.get(4))
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Define the codec and create VideoWriter 
            framerate = 17 # Same as original video
            output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,framerate, (width,height))

            ret, frame = capture.read() # start reading
            countFrame = 1 # first frame

            while ret:
                if countFrame<startPoint:
                    pass
                else:
                    output.write(frame)
                ret, frame = capture.read()
                countFrame += 1     
            
            capture.release()
            output.release()
        else:
            return

    elif mode =='timeLapse':
        # !!adjust fps to speedup the video!!

        # duration = frame_count/fps >>>> frame_count = fps*duration >>>>> fps = frame_count / duration
        fpsExpect = int(videoData['frameCount']/durTarget)

        if videoData['durationSec'] > durTarget:
            # Start Capture reading video
            capture = cv2.VideoCapture(fileInput) 
            width = int(capture.get(3))
            height = int(capture.get(4))
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Define the codec and create VideoWriter 
            output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,fpsExpect, (width,height))

            ret, frame = capture.read() # start reading
            while ret:
                output.write(frame)
                ret, frame = capture.read()

            capture.release()
            output.release()
        
        else:
            return

if __name__ == '__main__':
    main()