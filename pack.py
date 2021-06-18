import cv2
import numpy as np
import os
import time
import sys
import shutil
import base64
import json
from pyzbar.pyzbar import decode
import re


MONTH = {1:'JAN',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

WINDOW_NAME = 'Screen'
INTERFRAME_WAIT_MS = 1

CAMERA = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only

#cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
#cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

FONT = cv2.FONT_HERSHEY_SIMPLEX

FRAMERATE = 30 # Frame rate must be match with the camera


def main():
    currentTime = getCurrentTime()
    epochTime = time.time()

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
    for folderName, subfolders, filenames in os.walk(videoDir):
        #print('The current folder is ' + folderName)
        #print("Created: %s" % time.ctime(os.path.getctime(folderName)))

        # for subfolder in subfolders:
            # print('SUBFOLDER OF ' + folderName + ': ' + subfolder)

        for filename in filenames:
            print('FILE INSIDE ' + folderName + ': '+ filename)
            absPath = os.path.join(folderName,filename)
            # modTime = time.ctime(os.path.getmtime(absPath))
            # creTime = time.ctime(os.path.getctime(absPath))
            #modTime = os.path.getmtime(absPath)
            creTime = os.path.getctime(absPath)
            #print("Last modified: {}".format(modTime))
            diffTime = epochTime - creTime
            #print("Created: {}".format(creTime))
            #print('Current time: {}'.format(epochTime))
            print('File was create {} min ago'.format(int(diffTime/60)))

        # time in second
            OneMonth = 2628000
            #twoMonth = 5256000
            #threeMonth = 7884000

        # Remove the file that last more than desire time
    
            if diffTime > OneMonth: # time in second 
                os.unlink(absPath)

    while True: # loop this forever
        # recording status
        Record = False

        # Wait for QR code for staffID and order number to begin recording video
        try:
            Record , staffID , orderNo = QRscan()

        # Or manually exit here (check condition in QR scan function)
        except TypeError: # Return None type from QRscan function raise TypeError
            print('Exiting program')
            break

        # Information of order number and staff ID from qr code
        qrRead = {'staff': staffID ,'order': orderNo }

        # Start recording
        while Record:

            print(qrRead['staff'])
            print(qrRead['order'])

            # Create valid filename: First 4 character of ordernumber follow by date:time
            filename =  qrRead['order'][:5] + '_'+ str(currentTime['day']) + '_' + currentTime['monthName'] + '_' + str(currentTime['year'])

            ######## Start Recording Video ##########
    
            # Return file name and finish time to use to label video filename
            recVid , finishTime = recordingVdo(filename = filename,orderNo=qrRead['order'])

            
            originalFilename = recVid + '_original.avi'

            # Cut Footage
            # Get FPS data duration of the video
            vidData = getDurationFPS(fileInput=originalFilename)

            # Cut the duration of video
            print('Processing video....')
            vidCutName = cutVideo(fileInput=originalFilename,filename=filename,videoData=vidData,durTarget=180,mode='cut')

            # Add text and logo timestamp of finish process
            vidEditName = editVideo(fileInput=vidCutName,filename=filename,id=qrRead,logoDir=logoDir,timeFinish=finishTime)
            print('Video editing done!')

            ######## Video recording success (and editing too) ##########

            Record = False

            ######## Move file to valid folder and delete original file ##########

            # Move final editing video file to valid folder and delete the original
            # Current directory is the folder that run this script
            finishFilePath = os.path.join(parentDir,vidEditName)
            fileStorePath = os.path.join(currentMontVdo,vidEditName) # !! This is the location of the final video output
            shutil.copy(finishFilePath,fileStorePath)

            #delete original video
            filePathOri = os.path.join(parentDir,originalFilename)
            cutPathOri = os.path.join(parentDir,vidCutName)

            print(f'Deleting...{originalFilename}')
            os.unlink(filePathOri)
            if vidCutName != originalFilename:
                print(f'Deleting...{vidCutName}')
                os.unlink(cutPathOri)
            print(f'Deleting....{vidEditName}')
            os.unlink(finishFilePath)

            ######## Finish moving and deleting file ##########

            ######## Create video data and send to storage server ##########

            # Create information for video
            data = {}
            # Open recent video record to read and encode to BASE64
            with open(fileStorePath, mode='rb') as file:
                videoData = file.read()
            # Store video data
            data['videoData'] = base64.encodebytes(videoData).decode('utf-8')

            # Strore other information
            data['videoName'] , data['fileType'] = os.path.splitext(vidEditName) # Extract file name and type
            data['fileSize'] = os.path.getsize(fileStorePath)
            data['dateCreate'] = time.ctime(os.path.getctime(fileStorePath))
            data['staffID'] = qrRead['staff']
            data['orderNo'] = qrRead['order']
            
            # Pack data into JSON Object
            jsonData = json.dumps(data)

            # with open('json.txt', 'w') as f:
            #     f.write(jsonData)

            ######## Create video data and send to storage server ##########


            ######## Ask thse same staff if they want to packing more ##########

            Record , qrRead = recordAgain(QRinput = qrRead)
            # exit = input("Exit(y/n)")
            # print(exit.upper())
            # if exit.upper() == 'Y':
            #     break
    
    CAMERA.release()
    cv2.destroyAllWindows()
    sys.exit()

def getCurrentTime():
    currentTime = {}
    t = list(time.localtime())
    currentTime['year'] = t[0]
    currentTime['month'] = t[1]
    currentTime['monthName'] = MONTH[t[1]]
    currentTime['day'] = t[2]
    currentTime['hour'] = t[3]
    currentTime['min'] = t[4]
    return currentTime

def recordingVdo(filename,orderNo):
    # Start Capture raw footage
    #capture = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only
    width = int(CAMERA.get(3))
    height = int(CAMERA.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #FRAMERATE = 17 # FRAMERATE must be matach with the camera. See specification !!
    finish = False
    #font = cv2.FONT_HERSHEY_SIMPLEX 

    count = 0 # for flickering text
    showText = True
    numFrame = 10 # number of frame for flickering text
    
    
    # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    output = cv2.VideoWriter(filename+'_original.avi',fourcc,FRAMERATE,(width,height))

    start_time = time.time() # Start time counter

    while not finish:
        isTrue, oriframe = CAMERA.read()
        output.write(oriframe)

        editFrame , finish = scanToExit(oriframe,orderNo)

        if showText == True:
            editFrame = cv2.putText(editFrame,'Recording',(int(editFrame.shape[1]*0.75),50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
            count += 1
        elif showText == False:
            count += 1
        if (count > numFrame) and (showText == True):
            showText = False
            count = 0
        if (count > numFrame) and (showText == False):
            showText = True
            count = 0

        # Show time counter on the video #
        current_time = time.time()
        hours, rem = divmod(current_time-start_time, 3600)
        minutes, seconds = divmod(rem, 60)
        time_text = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)
        editFrame = cv2.putText(editFrame,time_text,(0,50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)

        cv2.imshow(WINDOW_NAME,editFrame)
        cv2.waitKey(INTERFRAME_WAIT_MS)

    
    finishTime = getCurrentTime() # get finish time to label to video

    # display finish status for 5 second then exit
    displayFrame = FRAMERATE * 5
    

    for frame in range(displayFrame):
        isTrue, display = CAMERA.read()
        display , _ = scanToExit(display,orderNo) # still display order no.
        cv2.putText(display,'Finished!',(0,50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
        cv2.putText(display,'Stop recording'+'.'*int(frame/FRAMERATE),(0,80),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
        cv2.imshow(WINDOW_NAME,display)
        cv2.waitKey(INTERFRAME_WAIT_MS)


    #capture.release()
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
    #FRAMERATE = 17 # Same as original video
    output = cv2.VideoWriter(videoName,fourcc,FRAMERATE, (width,height))
    
    #Reading one frame and move pointer to the next frame
    ret, frame = capture.read() # start reading

    while ret: # ret return True if the frame reading is success. 
        #waitScreen(mode ='edit')
        # Put the text in image 
        #font = cv2.FONT_HERSHEY_SIMPLEX # adjust font type
        textLocation_staff = (0,frame.shape[0]-10)  # adjust the minus value to move the row
        textLocation_order = (0,frame.shape[0]-30)  # adjust the minus value to move the row
        textLocation_finishTime = (0,frame.shape[0]-50)

        text_staff = 'Staff ID: '+id['staff']
        text_order = 'Order No: '+id['order']
        text_finishTime = 'Finish Time {}:{} {} {} {}'.format(timeFinish['hour'],timeFinish['min'],
                                                        timeFinish['day'],timeFinish['monthName'],timeFinish['year'])

        cv2.putText(img = frame,text=text_staff,org=textLocation_staff, 
                    fontFace=FONT, fontScale=0.5, color=(0, 255, 150), thickness=1, lineType =cv2.LINE_AA)
        cv2.putText(img = frame,text=text_order,org=textLocation_order,
                    fontFace=FONT, fontScale=0.5, color=(0, 255, 150), thickness= 1, lineType=cv2.LINE_AA)
        cv2.putText(img = frame,text=text_finishTime ,org=textLocation_finishTime,fontFace=FONT, fontScale=0.5, color=(255, 245, 0), thickness= 1, lineType=cv2.LINE_AA)
        
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

    # print('fps = ' + str(fps))
    # print('number of frames = ' + str(frame_count))
    # print('duration (S) = ' + str(duration))
    # minutes = int(duration/60)
    # seconds = duration%60
    # print('duration (M:S) = ' + str(minutes) + ':' + str(seconds))

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
        #fps = 17 # <<<<<!!!! adjust this value depend on the camera
        numFrameExpect = FRAMERATE * durTarget

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
            #FRAMERATE = 17 # Same as original video
            filename = f'{filename}_cut.avi'  # change file name here
            #output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,FRAMERATE, (width,height))
            output = cv2.VideoWriter(filename,fourcc,FRAMERATE, (width,height))

            ret, frame = capture.read() # start reading
            countFrame = 1 # first frame

            while ret:
                if countFrame<startPoint:
                    #waitScreen()
                    pass
                else:
                    #waitScreen()
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
                #waitScreen()
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

    # Create a mask of logo and create its inverse mask also
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

def QRscan(staffStatus=False,orderStatus=False):
    ##### This is IDLE state (starting point) that alway return to  #####
    ## Return video capture object class from this function ##

    #capture = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only

    # Regrex to identify  staff number and ordernumber
    # Staff ID format: Ex 1110
    staffPattern = '1110'
    
    # Order number format : ex DSG
    orderPattern = 'DSG'

    delay = 0
    #FRAMERATE = 17

    while True:
        ret,frame = CAMERA.read()
        #font = cv2.FONT_HERSHEY_SIMPLEX

        # Ask for staff ID first
        if not staffStatus:
            cv2.putText(frame,'Please Scan Staff ID',(0,30),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            try:
                staffStatus , staffID = decodeStaffID(frame) # if found ID return True status
                #print(staffID)
            except TypeError: # if function return None (no QR code found) must handle TypeError
                #print('Not detect staff ID yet')
                pass

        # Then ask for order number or start another packing process for the same staff
        if staffStatus and not orderStatus:
            cv2.putText(frame,'Please Scan Staff ID',(0,30),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            cv2.putText(frame,'Found',(400,30),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)

            cv2.putText(frame,'Please Order number',(0,60),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            
            # Still showing QR code detect but not care for output
            decodeStaffID(frame)

            try:
                orderStatus , orderID = decodeOrderID(frame)
                #print(orderID)
            except TypeError: # if function return None (no QR code found) must handle TypeError
                #print('Not detect order number yet')
                pass
    
                # else:
                #     # get the point of the polygon
                #     points = np.array([code.polygon],np.int32)
                #     points = points.reshape((-1,1,2))
                #     # polyline is 3 dimension array 
                #     # 1 dimension represent each group of polygon (no line cross between group)
                #     # 2 dimension represent each point of the polygon in group
                #     # 3 dimension represent location of the point (pixel row,column)
                #     # [points] = Array of polygonal curves. There may be multiple QR detect
                #     cv2.polylines(frame,[points],True,(0,0,255),5) 
                #     # get the rectangle data (left , top , width , height)
                #     rect = code.rect
                #     # origin point(top-left) of the rectangle
                #     rectOrigin = (rect[0],rect[1])
                #     # Adjust text to middle buttom point of the  rectangle
                #     # bottom point(bottom-left) of the rectangle : origin + height
                #     rectButtom = (rect[0]+int(rect[2]*0.3),rect[1]+rect[3]+30)
                #     cv2.putText(frame,qrCode,rectOrigin,fontFace=font,fontScale=1,color=(0,0,255),thickness=2)
                #     cv2.putText(frame,'Invalid',rectButtom,fontFace=font,fontScale=1,color=(0,0,255),thickness=2)

        # After recieve both ID and order number. Show status for some time before start recording
        if staffStatus and orderStatus:
            cv2.putText(frame,'Please Scan Staff ID',(0,30),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            cv2.putText(frame,'Found',(400,30),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)

            cv2.putText(frame,'Please Order number',(0,60),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            cv2.putText(frame,'Found',(400,60),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)

            

            # Still showing QR code detect but not care for output
            decodeStaffID(frame)
            decodeOrderID(frame)

            # still showing display for a moment befor exiting function
            delay += 1
            if delay < 50:
                cv2.putText(frame,'Start Recording' +'.'*int(delay/10),(0,90),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
                cv2.imshow(WINDOW_NAME,frame)
                cv2.waitKey(INTERFRAME_WAIT_MS)
                continue
            else:
                cv2.putText(frame,'Start Recording' +'.'*int(delay/10),(0,90),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
                cv2.imshow(WINDOW_NAME,frame)
                cv2.waitKey(INTERFRAME_WAIT_MS)
                #capture.release()
                #cv2.destroyAllWindows()
                return True , staffID , orderID

        cv2.imshow(WINDOW_NAME,frame)

        ### Manually exit here ###
        if cv2.waitKey(INTERFRAME_WAIT_MS) & 0xFF == ord('q'):
            return 

def decodeStaffID(frame):
    # Scan for staff ID number then border the rectangle and put text on the screen 
    #font = cv2.FONT_HERSHEY_SIMPLEX
    for code in decode(frame):
        qrCode = code.data.decode('utf-8')
        if QRregex(inputQR=qrCode,mode='staff'): # Detect qrcode if match pattern
            #cv2.putText(frame,'Found',(400,30),fontFace=font,fontScale=1,color=(0,255,0),thickness=2)
            # get the point of the polygon
            points = np.array([code.polygon],np.int32)
            points = points.reshape((-1,1,2))
            # polyline is 3 dimension array 
            # 1 dimension represent each group of polygon (no line cross between group)
            # 2 dimension represent each point of the polygon in group
            # 3 dimension represent location of the point (pixel row,column)
            # [points] = Array of polygonal curves. There may be multiple QR detect
            cv2.polylines(frame,[points],True,(0,255,0),5) 
            # get the rectangle data (left , top , width , height)
            rect = code.rect
            # origin point(top-left) of the rectangle
            rectOrigin = (rect[0],rect[1])
            # Adjust text to middle buttom point of the  rectangle
            # bottom point(bottom-left) of the rectangle : origin + height
            rectButtom = (rect[0]+int(rect[2]*0.3),rect[1]+rect[3]+30)
            cv2.putText(frame,qrCode,rectOrigin,fontFace=FONT,fontScale=1,color=(255,0,255),thickness=2)
            cv2.putText(frame,'Staff ID',rectButtom,fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            return True , qrCode
        else:
            continue

def decodeOrderID(frame):
    # Scan for order number then border the rectangle and put text on the screen 
    #font = cv2.FONT_HERSHEY_SIMPLEX
    for code in decode(frame):
        qrCode = code.data.decode('utf-8')
        # Detecting  for order number
        if QRregex(inputQR=qrCode,mode='order'):
            #cv2.putText(frame,'Found',(400,60),fontFace=font,fontScale=1,color=(0,255,0),thickness=2)
            points = np.array([code.polygon],np.int32)
            points = points.reshape((-1,1,2))
            cv2.polylines(frame,[points],True,(0,255,0),5) 
            rect = code.rect
            rectOrigin = (rect[0],rect[1])
            rectButtom = (rect[0]+int(rect[2]*0.3),rect[1]+rect[3]+30)
            cv2.putText(frame,qrCode,rectOrigin,fontFace=FONT,fontScale=1,color=(255,0,255),thickness=2)
            cv2.putText(frame,'Order number',rectButtom,fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            return True , qrCode
        else:
            continue  

def scanToExit(frame,orderNo):
    # In record function call this to implement scaning order number to end the recording process

    #font = cv2.FONT_HERSHEY_SIMPLEX
    text = 'Scan order QRcode again to stop recording after finish packing'
    cv2.putText(frame,text,(0,frame.shape[0]-10),fontFace=FONT,fontScale=0.5,color=(255,0,255),thickness=1)
    for code in decode(frame):
        qrCode = code.data.decode('utf-8')
        #print(qrCode)
        # Detecting  for order number
        if qrCode == orderNo:
            points = np.array([code.polygon],np.int32)
            points = points.reshape((-1,1,2))
            cv2.polylines(frame,[points],True,(0,255,0),5) 
            rect = code.rect
            rectOrigin = (rect[0],rect[1])
            rectButtom = (rect[0]+int(rect[2]*0.3),rect[1]+rect[3]+30)
            cv2.putText(frame,qrCode,rectOrigin,fontFace=FONT,fontScale=1,color=(255,0,255),thickness=2)
            cv2.putText(frame,'Order number',rectButtom,fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            return frame , True
        else:
            #detect invalid number (not order number)
            points = np.array([code.polygon],np.int32)
            points = points.reshape((-1,1,2))
            cv2.polylines(frame,[points],True,(0,0,255),5) 
            rect = code.rect
            rectOrigin = (rect[0],rect[1])
            rectButtom = (rect[0]+int(rect[2]*0.3),rect[1]+rect[3]+30)
            cv2.putText(frame,qrCode,rectOrigin,fontFace=FONT,fontScale=1,color=(0,0,255),thickness=2)
            cv2.putText(frame,'Invalid',rectButtom,fontFace=FONT,fontScale=1,color=(0,0,255),thickness=2)
            continue 

    return frame , False

def recordAgain(QRinput):
    # Information of order number and staff ID from qr code
    # QRinput is dictionary {'staff': staffID ,'order': orderNo }

    #font = cv2.FONT_HERSHEY_SIMPLEX 
    #capture = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only
    
    count = 0 # for flickering text
    showText = True
    numFrame = 10 # number of frame for flickering text

    while True:
        ret,frame = CAMERA.read()
        frame = cv2.putText(frame,'Staff ID :' + QRinput['staff'] ,(0,50),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
        if showText == True:
            frame = cv2.putText(frame,'Waiting for next QR order',(0,100),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
            count += 1
        elif showText == False:
            count += 1
        if (count > numFrame) and (showText == True):
            showText = False
            count = 0
        if (count > numFrame) and (showText == False):
            showText = True
            count = 0

        frame = cv2.putText(frame,'Scan Staff ID to log off' ,(0,frame.shape[0]-20),fontFace=FONT,fontScale=1,color=(0,0,255),thickness=2)

        # scan new order number to begin record next package
        try:
            detectOrder , orderNum = decodeOrderID(frame) 
            if detectOrder:
                QRinput['order'] = orderNum  # Get the next order number 

                # Display Status after detect order number 
                displayFrame = FRAMERATE * 5   # duration of  status screen (in second)
                for frame in range(displayFrame):
                    isTrue, display = CAMERA.read()
                    decodeOrderID(display)
                    cv2.putText(display,'Next order Found!',(0,50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
                    cv2.putText(display,'Order no: '+ QRinput['order'],(0,100),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
                    # Flickering text
                    if showText == True:
                        cv2.putText(display,'Restarting',(0,display.shape[0]-30),fontFace=FONT,fontScale=1,color=(0,0,255),thickness=2)
                        count += 1
                    elif showText == False:
                        count += 1
                    if (count > numFrame) and (showText == True):
                        showText = False
                        count = 0
                    if (count > numFrame) and (showText == False):
                        showText = True
                        count = 0
                    cv2.imshow(WINDOW_NAME,display)
                    cv2.waitKey(INTERFRAME_WAIT_MS)
                #capture.release()
                #cv2.destroyAllWindows()
                return True , QRinput
        except TypeError:
            pass

        # scan same staff ID to log off
        try: 
            logOff , staffID = decodeStaffID(frame)
            if (logOff) and (staffID == QRinput['staff']):
                 # Display Status after detect order number 
                displayFrame = FRAMERATE * 5   # duration of  status screen (in second)
                for frame in range(displayFrame):
                    isTrue, display = CAMERA.read()
                    decodeStaffID(display)
                    cv2.putText(display,'Detect Staff ID ' + staffID,(0,50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
                    cv2.putText(display,'Finished Job ',(0,100),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
                    # Flickering text
                    if showText == True:
                        cv2.putText(display,'Logging off',(0,display.shape[0]-30),fontFace=FONT,fontScale=1,color=(0,0,255),thickness=2)
                        count += 1
                    elif showText == False:
                        count += 1
                    if (count > numFrame) and (showText == True):
                        showText = False
                        count = 0
                    if (count > numFrame) and (showText == False):
                        showText = True
                        count = 0
                    cv2.imshow(WINDOW_NAME,display)
                    cv2.waitKey(INTERFRAME_WAIT_MS)
                #capture.release()
                #cv2.destroyAllWindows()
                return False , QRinput
        except TypeError:
            pass

        cv2.imshow(WINDOW_NAME,frame)
        cv2.waitKey(INTERFRAME_WAIT_MS)

def waitScreen(mode):

    ## note wait screen make video edit longer##
    if mode == 'edit':
        _, waitFrame = CAMERA.read()
        waitFrame = cv2.putText(waitFrame,'Editing video',(0,30),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
        waitFrame = cv2.putText(waitFrame,'Please wait',(0,60),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
        cv2.imshow(WINDOW_NAME,waitFrame)
        cv2.waitKey(1)
    elif mode == 'cut':
        _, waitFrame = CAMERA.read()
        waitFrame = cv2.putText(waitFrame,'Cutting video',(0,30),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
        waitFrame = cv2.putText(waitFrame,'Please wait',(0,60),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
        cv2.imshow(WINDOW_NAME,waitFrame)
        cv2.waitKey(1)

def QRregex(inputQR,mode):

    ##### Create Regular Expression to dectect pattern for Staff ID and Order number ####

    ### Regex object for Staff ID ###
    # Temporary for testing purpose not final
    # Example : Staff ID  = 3 character (uppercase) follow by 5 digit  : PAC62578
    staff_ID_regex = re.compile(r'''(
                                        ([A-Z]{3})      # first 3 letter in uppercase
                                        (\d{5})         # 5 digit
                                        )''',re.VERBOSE)

    ## Regex object for order number ##
    # Temporary for testing purpose not final
    # Example : Order number  = 3 charracter (uppercase) follow by - and 3 digit follow by any  5 character/digit    
    #  ex: QA-375bx59ah

    order_number_regex = re.compile(r'''(
                                    ([A-Z]{2})      # first 2 letter
                                    -               # - symbol
                                    (\d{3})         # 3 digit
                                    (.{5})          # any 5 character
                                        )''',re.VERBOSE)

    # select which QR to detect (Staff or order number)
    # 2 mode 'staff' and 'order'
    if (mode == 'staff'):
        staff_mo = staff_ID_regex.search(inputQR)
        if staff_mo != None:
            #print(staff_mo.group())
            return True
        else:
            #print('Invalid')
            return False

    elif (mode =='order'):
        order_mo = order_number_regex.search(inputQR)
        if order_mo != None:
            #print(order_mo.group())
            return True
        else:
            #print('Invalid')
            return False
    else:
        print('Invalid mode')
        return False


if __name__ == '__main__':
    main() # Run script
    #inputQR = input('enter test: ')
    #QRregex(inputQR,mode='order')
    
    
    