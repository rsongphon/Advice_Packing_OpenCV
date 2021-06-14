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
    logoDir = os.path.join(parentDir,'logo')

    if not os.path.exists(videoDir):
        os.makedirs(videoDir)
    if not os.path.exists(currentMontVdo):
        os.makedirs(currentMontVdo)
    
    # Check the folder of video that last more than 1 month
    # recording status
    startRecord = False

    while True:
        # Information of order number and staff ID from qr code
        qrRead = {'staff':'11100215XF','order':'DSGA45D'}

        # Create valid filename: First 4 character of ordernumber follow by date:time
        filename =  qrRead['order'][:5] + '_'+ str(currentTime['day']) + '_' + currentTime['monthName'] + '_' + str(currentTime['year'])
        
        # Return file name and finish time to use to label video filename
        recVid , finishTime = recordingVdo(filename = filename)
        originalFilename = recVid + '_original.avi'

        # Cut Footage
        # Get FPS data duration of the video
        vidData = getDurationFPS(fileInput=originalFilename)
        # Cut the duration of video
        vidCutName = cutVideo(fileInput=originalFilename,filename=filename,videoData=vidData,durTarget=180,mode='cut')

        # Add text and logo timestamp of finish product
        vidEditName = editVideo(fileInput=vidCutName,filename=filename,id=qrRead,logoDir=logoDir,timeFinish=finishTime)

        

        

        

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

def recordingVdo(filename):
    # Start Capture raw footage
    capture = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only
    width = int(capture.get(3))
    height = int(capture.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    framerate = 17 # Framerate must be matach with the camera. See specification !!

    
    
    # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    output = cv2.VideoWriter(filename+'_original.avi',fourcc,framerate,(width,height))
    while True:
        isTrue, frame = capture.read()
        output.write(frame)
        cv2.imshow('frame',frame)

        # read QR code or push button to break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    finishTime = getCurrentTime()
    capture.release()
    output.release()
    cv2.destroyAllWindows()

    return filename, finishTime

def editVideo(fileInput,filename,id,logoDir,timeFinish):

    videoName = filename+'.avi'
    # Start Capture raw footage
    capture = cv2.VideoCapture(fileInput) 
    width = int(capture.get(3))
    height = int(capture.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Define the codec and create VideoWriter 
    framerate = 17 # Same as original video
    output = cv2.VideoWriter(videoName,fourcc,framerate, (width,height))
    
    #Reading one frame and move pointer to the next frame
    ret, frame = capture.read() # start reading

    while ret: # ret return True if the frame reading is success. 

        # Put the text in image 
        font = cv2.FONT_HERSHEY_SIMPLEX # adjust font type
        textLocation_staff = (0,frame.shape[0]-10)  # adjust the minus value to move the row
        textLocation_order = (0,frame.shape[0]-30)  # adjust the minus value to move the row
        textLocation_finishTime = (0,frame.shape[0]-50)

        text_staff = 'Staff ID: '+id['staff']
        text_order = 'Order No: '+id['order']
        text_finishTime = 'Finish Time {}:{} {} {} {}'.format(timeFinish['hour'],timeFinish['min'],
                                                        timeFinish['day'],timeFinish['monthName'],timeFinish['year'])

        cv2.putText(img = frame,text=text_staff,org=textLocation_staff, 
                    fontFace=font, fontScale=0.5, color=(0, 255, 150), thickness=1, lineType =cv2.LINE_AA)
        cv2.putText(img = frame,text=text_order,org=textLocation_order,
                    fontFace=font, fontScale=0.5, color=(0, 255, 150), thickness= 1, lineType=cv2.LINE_AA)
        cv2.putText(img = frame,text=text_finishTime ,org=textLocation_finishTime,fontFace=font, fontScale=0.5, color=(255, 245, 0), thickness= 1, lineType=cv2.LINE_AA)
        
        #Put logo in the image
        logoAbsPath = os.path.join(logoDir,'advice.jpg') # Change logo here
        logo = cv2.imread(logoAbsPath)
        
        frame = addLogo(frame,logo,logoScale=0.1)

        output.write(frame)
        ret, frame = capture.read() # next frame

    capture.release()
    output.release()
    return videoName

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

def cutVideo(fileInput,filename,videoData,durTarget,mode='cut'):
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
            filename = f'{filename}_cut.avi'  # change file name here
            #output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,framerate, (width,height))
            output = cv2.VideoWriter(filename,fourcc,framerate, (width,height))

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

            return filename
        else:
            return fileInput # return the original videoname incase video did not change

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
            filename = f'{filename}_timelapse.avi'  # change file name here
            #output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,fpsExpect, (width,height))
            output = cv2.VideoWriter(filename,fourcc,fpsExpect, (width,height))

            ret, frame = capture.read() # start reading
            while ret:
                output.write(frame)
                ret, frame = capture.read()

            capture.release()
            output.release()
            return filename 
        
        else:
            return fileInput # return the original videoname incase video did not change

def addLogo(inputFrame,imgLogo,logoScale=0.1): 

    def rescaleFrame(frame,scale=logoScale): 
        # work for image , video , live camera
        #The shape of an image is accessed by img.shape. It returns a tuple of the number of rows, columns, and channels (if the image is color):
        width = int(frame.shape[1] * scale)  # shape[1] = width: must be int
        height = int(frame.shape[0]* scale) # shape[0] = :height must be int

        dimension = (width,height) # tuple to keep dimension

        return cv2.resize(frame,dimension,interpolation=cv2.INTER_AREA)

    oriFrame = inputFrame
    logo = imgLogo

    logoResize = rescaleFrame(logo,logoScale) # resize

    height,width,channels = logoResize.shape # get access to the dimension of the logo

    # Create ROI to put logo into
    roi = oriFrame[0:height, 0:width]

    # Now create a mask of logo and create its inverse mask also
    logo2gray = cv2.cvtColor(logoResize, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(logo2gray, 10, 255, cv2.THRESH_BINARY)
    maskInv = cv2.bitwise_not(mask)

    # black-out the area of logo in ROI
    imgBg = cv2.bitwise_and(roi, roi, mask=maskInv)

    # Take only region of logo from logo image.
    logoFg = cv2.bitwise_and(logoResize, logoResize, mask=mask)

    # add logo and background together
    finalImg = cv2.add(imgBg,logoFg)

    # Modify the original , Specify the location!
    oriFrame[0:height,0:width] = finalImg

    return oriFrame





if __name__ == '__main__':
    main()