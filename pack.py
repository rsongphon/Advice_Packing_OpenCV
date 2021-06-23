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
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import *
import skimage.exposure


MONTH = {1:'JAN',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

WINDOW_NAME = 'Screen'
INTERFRAME_WAIT_MS = 1

CAMERA = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only
#CAMERA = cv2.VideoCapture(0) # window only

CAMERA.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
CAMERA.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


#cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
#cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

FONT = cv2.FONT_HERSHEY_DUPLEX

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

    wait_time_start = time.time() # Start countdown time

    while True: # loop this forever

        

        # recording status
        Record = False

        # Wait for QR code for staffID and order number to begin recording video
        try:
            Record , staffID , orderNo = QRscan(start_time=wait_time_start)

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
            edit_videoname , original_videoname , finishTime = recordingVdo(filename = filename,qrRead=qrRead,logo_directory = logoDir)

            # Cut Footage
            # Get FPS data duration of the video
            video_data = getDurationFPS(fileInput=edit_videoname)

            # Cut the duration of video
            print('Start cutting video...')
            cut_time_start = time.time()
            cutVideo(file_inputname=edit_videoname,videoData=video_data,durTarget=180,mode='cut')
            cut_end_time = time.time()
            cut_time = cut_end_time - cut_time_start
            hours, rem = divmod(cut_time, 3600)
            minutes, seconds = divmod(rem, 60)
            time_text = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)
            print('Cutting video Done...')
            print('Cut time: ',end='')
            print(time_text)
            
            ######## Video recording success (and editing too) ##########

            Record = False

            ######## Move file to valid folder and delete original file ##########

            # Move final editing video file to valid folder and delete the original
            # Current directory is the folder that run this script
            finishFilePath = os.path.join(parentDir,edit_videoname)
            fileStorePath = os.path.join(currentMontVdo,edit_videoname) # !! This is the location of the final video output
            shutil.copy(finishFilePath,fileStorePath)

            #delete original video
            filepath_original = os.path.join(parentDir,original_videoname)
            print(f'Deleting backup...{original_videoname}')
            os.unlink(filepath_original)
            print(f'Deleting backup....{edit_videoname}')
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
            data['videoName'] , data['fileType'] = os.path.splitext(edit_videoname) # Extract file name and type
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
            
            wait_time_start = time.time() # Reset countdown time

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

def recordingVdo(filename,qrRead,logo_directory):
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

    # Backup file 
    ori_filename = filename+'_original.avi'

    # filename foe use in the next process

    edit_filename = filename+'.avi'
    
    # Define the codec and create VideoWriter object.
    output = cv2.VideoWriter(ori_filename,fourcc,FRAMERATE,(width,height))
    output_edit = cv2.VideoWriter(edit_filename,fourcc,FRAMERATE,(width,height))

    start_time = time.time() # Start time counter

    # For using to delay qrcode to exit the recording progress
    QR_counter_frame = 0
    QR_detect_duration = 0 # in second
    # CHANE DELAY TO SCAN EXIT HERE
    duration_exit_limit = 5  # in second 
    
    count_to_reset = 0
    QR_absent_duration = 0
    # CHANE DELAY RESET COUNTDOWN TIME HERE
    QR_absent_limit = 3 # in second

    # Loop to record video
    # To exit video: show QR code to start countdown process
    # Countdown is count every frame that detect QR code of the package
    # When countdown reach the limit exit loop and stop recording 
    # But! if QR code is absent for long period of time. Reset the counter to countdown to zero 
    # So that when we scan again. It does not continue frome last contdown (Start from zero again)
    # duration = frame_count/fps
    while QR_detect_duration<duration_exit_limit:
        isTrue, oriframe = CAMERA.read()
        output.write(oriframe)
        oriframe_copy = oriframe.copy()
        frame_forshow = oriframe.copy()
        edit_frame = editVideo(frameInput=oriframe_copy,id=qrRead,logoDir=logo_directory)
        output_edit.write(edit_frame)

        show_frame , detect = scanToExit(frame_forshow,qrRead['order'])

        # When detect QR code start counting frame and convert to second (countdown)
        if detect:
            QR_counter_frame += 1
            QR_detect_duration = QR_counter_frame/FRAMERATE   # convert frame to duration in second
            #print(QR_detect_duration)
            # show exit bar progress
            percent_exit = (QR_detect_duration * 100) / duration_exit_limit
            show_frame = cv2.putText(show_frame,'exit',(int(show_frame.shape[1]*0.5),50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
            show_frame = cv2.putText(show_frame,str(int(percent_exit)) + '%' ,(int(show_frame.shape[1]*0.5),100),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
            # If there is some QR code frame detect. Must not reset the counter 
            count_to_reset = 0
            
        # IF QR code is absent from frame start counting time to reset countdown
        if not detect:
            # start read time 
            count_to_reset += 1
            QR_absent_duration = count_to_reset/FRAMERATE
            #print(QR_absent_duration)
        # If QR code absent from frame more than set time with no detecton whatsoever. reset counter (countdown)
        if QR_absent_duration > QR_absent_limit: # Adjust the accuracy here : less value = more error : more value 
            QR_counter_frame = 0
            count_to_reset = 0

        # show recording status
        if showText == True:
            show_frame = cv2.putText(show_frame,'Recording',(int(show_frame.shape[1]*0.75),50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
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
        show_frame = cv2.putText(show_frame,time_text,(0,50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)

        cv2.imshow(WINDOW_NAME,show_frame)
        cv2.waitKey(INTERFRAME_WAIT_MS)

    
    finishTime = getCurrentTime() # get finish time to label to video

    # display finish status for 5 second then exit
    displayFrame = FRAMERATE * 5
    

    for frame in range(displayFrame):
        isTrue, display = CAMERA.read()
        display , _ = scanToExit(display,qrRead['order']) # still display order no.
        cv2.putText(display,'Finished!',(0,50),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
        cv2.putText(display,'Stop recording'+'.'*int(frame/FRAMERATE),(0,80),fontFace=FONT,fontScale=1,color=(0,255,0),thickness=2)
        cv2.imshow(WINDOW_NAME,display)
        cv2.waitKey(INTERFRAME_WAIT_MS)


    #capture.release()
    output.release()
    #cv2.destroyAllWindows()

    return edit_filename, ori_filename , finishTime

def editVideo(frameInput,id,logoDir):

    # # Convert to gray scale image (use for thresholding)
    # gray_frame = cv2.cvtColor(frameInput,cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray',gray_frame)
    # # Threshholding image to identify dark area
    # thresholding ,thresh_image = cv2.threshold(gray_frame,150,255,cv2.THRESH_BINARY)
    # cv2.imshow('Thresh',thresh_image)

    # # Pixel black > text white

    # # Pixel white > text black

    # Put the text in image 
    #font = cv2.FONT_HERSHEY_SIMPLEX # adjust font type
    textLocation_staff = (0,frameInput.shape[0]-10)  # adjust the minus value to move the row
    textLocation_order = (0,frameInput.shape[0]-30)  # adjust the minus value to move the row
    textLocation_Time = (0,frameInput.shape[0]-50)

    text_staff = 'Staff ID: '+id['staff']
    text_order = 'Order No: '+id['order']
    current_time = getCurrentTime()
    text_time = 'Time : Date {}:{} {} {} {}'.format(current_time['hour'],current_time['min'],current_time['day'],current_time['monthName'],current_time['year'])

    cv2.putText(img = frameInput,text=text_staff,org=textLocation_staff, 
                fontFace=FONT, fontScale=0.5, color=(255, 255, 0), thickness=4, lineType =cv2.LINE_AA)
    cv2.putText(img = frameInput,text=text_staff,org=textLocation_staff, 
                fontFace=FONT, fontScale=0.5, color=(0, 0, 0), thickness=1, lineType =cv2.LINE_AA)

    cv2.putText(img = frameInput,text=text_order,org=textLocation_order,
                fontFace=FONT, fontScale=0.5, color=(255, 255, 0), thickness= 4, lineType=cv2.LINE_AA)
    cv2.putText(img = frameInput,text=text_order,org=textLocation_order,
                fontFace=FONT, fontScale=0.5, color=(0, 0, 0), thickness= 1, lineType=cv2.LINE_AA)

    cv2.putText(img = frameInput,text=text_time ,org=textLocation_Time,fontFace=FONT, fontScale=0.5, color=(255, 255, 0), thickness= 4, lineType=cv2.LINE_AA)
    cv2.putText(img = frameInput,text=text_time ,org=textLocation_Time,fontFace=FONT, fontScale=0.5, color=(0, 0, 0), thickness= 1, lineType=cv2.LINE_AA)
    
    #Put logo in the image
    logoAbsPath = os.path.join(logoDir,'advice-logo.jpg') # Change logo here
    logo = cv2.imread(logoAbsPath)
    
    frameInput = addLogo(frameInput,logo,logoScale=0.1)

    return frameInput

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

def cutVideo(file_inputname,videoData,durTarget,mode='cut'):
    # Choose Between 2 mode 
    # 'cut' for cuting the footage into last desire duration
    # 'timeLapse' for speed up the video in desire duration

    if mode=='cut':
        print('Selecting mode.... Cut')
        # if duration more than we want (durTarget)

        # !!Count in second!!

        # cut the last footage to the value we want
        # duration = frame_count/fps >>>> frame_count = fps*duration
        #fps = 17 # <<<<<!!!! adjust this value depend on the camera
        numFrameExpect = FRAMERATE * durTarget

        if videoData['durationSec'] > durTarget:
            filename = f'{file_inputname}_cut.avi'
            #start_time = float((videoData['durationSec']/60) - 3.0)
            start_time = videoData['durationSec'] - 180
            print(start_time)
            #end_time = float(videoData['durationSec']/60)
            end_time = videoData['durationSec']
            print(end_time)


            ffmpeg_extract_subclip(file_inputname,start_time, end_time, targetname=filename)

            # Delete the original file
            os.unlink(file_inputname)
            # rename to original fileman
            shutil.move(filename,file_inputname)
            
            # Prototype code

            # print('Video lenght is {} minute . More than {} minute'.format(str(int(videoData['durationSec']/60)),str(int(durTarget/60))))
            # # Subtract actual video frame with expect frame to get checkpoint of the starting frame (last batch of the video)
            # startPoint = videoData['frameCount'] - numFrameExpect
            # #print(startPoint)

            # # Start Capture reading video
            # capture = cv2.VideoCapture(fileInput) 
            # width = int(capture.get(3))
            # height = int(capture.get(4))
            # fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Define the codec and create VideoWriter 
            # #FRAMERATE = 17 # Same as original video
            # filename = f'{filename}_cut.avi'  # change file name here
            # #output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,FRAMERATE, (width,height))
            # output = cv2.VideoWriter(filename,fourcc,FRAMERATE, (width,height))

            # ret, frame = capture.read() # start reading
            # countFrame = 1 # first frame

            # while ret:
            #     if countFrame<startPoint:
            #         #waitScreen()
            #         pass
            #     else:
            #         #waitScreen()
            #         output.write(frame)
            #     ret, frame = capture.read()
            #     countFrame += 1     
            
            # capture.release()
            # output.release()
            return 
        else:
            return 

    elif mode =='timeLapse':
        print('Selecting mode.... Timelapse')
        # !!adjust fps to speedup the video!!

        # duration = frame_count/fps >>>> frame_count = fps*duration >>>>> fps = frame_count / duration
        fpsExpect = int(videoData['frameCount']/durTarget)

        if videoData['durationSec'] > durTarget:
            # Start Capture reading video
            capture = cv2.VideoCapture(file_inputname) 
            width = int(capture.get(3))
            height = int(capture.get(4))
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Define the codec and create VideoWriter
            filename = f'{file_inputname}_timelapse.avi'  # change file name here
            #output = cv2.VideoWriter('cut{}min.avi'.format(str(durTarget/60)),fourcc,fpsExpect, (width,height))
            output = cv2.VideoWriter(filename,fourcc,fpsExpect, (width,height))

            ret, frame = capture.read() # start reading
            while ret:
                #waitScreen()
                output.write(frame)
                ret, frame = capture.read()

            capture.release()
            output.release()

            # Delete the original file
            os.unlink(file_inputname)
            # rename to original fileman
            shutil.move(filename,file_inputname)

            return  
        
        else:
            return # return the original videoname in case video did not change

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

    #mask = cv2.medianBlur(mask,13)
    #cv2.imshow('mask',mask)

    #maskInv = cv2.medianBlur(maskInv,13)
    #cv2.imshow('maskINV',maskInv)

    # black-out the area of logo in ROI
    imgBg = cv2.bitwise_and(roi, roi, mask=maskInv)
    #cv2.imshow('roi',imgBg)

    # Take only region of logo from logo image.
    logoFg = cv2.bitwise_and(logoResize, logoResize, mask=mask)
    #cv2.imshow('roi2',logoFg)

    # add logo and background together
    finalImg = cv2.add(imgBg,logoFg)
    #finalImg = cv2.GaussianBlur(finalImg,(5,5),0)
    #cv2.imshow('Before blur',finalImg)
    finalImg = cv2.medianBlur(finalImg,3)
    #cv2.imshow('after blur',finalImg)

    # Modify the original , Specify the location!
    oriFrame[0:height,0:width] = finalImg
    
    
    return oriFrame

def QRscan(start_time,staffStatus=False,orderStatus=False):
    ##### This is IDLE state (starting point) that alway return to  #####
    ## Return video capture object class from this function ##

    #capture = cv2.VideoCapture(0,cv2.CAP_DSHOW) # window only


    delay_frame = 0

    wait_time_sec = 3 ##### Change delay time before start recording here #####

    while True:
        ret,frame = CAMERA.read()
        #font = cv2.FONT_HERSHEY_SIMPLEX
        recent_time = time.time() # Get current time
        time_gap = recent_time - start_time 
        exit_time = 60 * 5  # Exit after 60 * (miniute)
        #print(time_gap)

        # Ask for staff ID first
        if not staffStatus:
            cv2.putText(frame,'Please Scan Staff ID',(0,30),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)

            if time_gap > exit_time:  # 
                print('No activity. Exiting program')
                break

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
            delay_frame += 1
            delay_second = delay_frame/FRAMERATE
            if delay_second < wait_time_sec:
                cv2.putText(frame,'Start Recording' +'...'*int(delay_second),(0,90),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
                for i in range(wait_time_sec):
                    if (i == int(delay_second)):
                        cv2.putText(frame,str((wait_time_sec+1) - (i+1)),(int(frame.shape[1]/2)-50,int(frame.shape[0]/2)+50),fontFace=FONT,fontScale=5,color=(0,255,0),thickness=5)
                cv2.imshow(WINDOW_NAME,frame)
                cv2.waitKey(INTERFRAME_WAIT_MS)
                continue
            else: # last frame
                cv2.putText(frame,'Start Recording' +'...'*int(delay_second),(0,90),fontFace=FONT,fontScale=1,color=(255,255,0),thickness=2)
                cv2.putText(frame,str((wait_time_sec+1)-int(delay_second)),(int(frame.shape[1]/2)-50,int(frame.shape[0]/2)+50),fontFace=FONT,fontScale=5,color=(0,255,0),thickness=5)
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
            points = points.reshape((-1,1,2)) # Open CV Document said to do so. but not neccessary
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
            points = points.reshape((-1,1,2))  # Open CV Document said to do so. but not neccessary
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

def putText(video_input,text,duration):

    # loading video dsa gfg intro video 
    clip = VideoFileClip(video_input) 
        
    # Generate a text clip 
    text_clip = TextClip(text, fontsize = 75, color = 'black') 
        
    # setting position of text and duration 
    text_clip = txt_clip.set_pos('center').set_duration(duration) 
        
    # Overlay the text clip on the first video clip 
    video = CompositeVideoClip([clip, text_clip]) 
        
    # showing video 
    video.ipython_display(width = 280) 

def test_blur():
        # load image with alpha channel
    img = cv2.imread('C:/Users/NB/Documents/GitHub/Advice_Packing_OpenCV/logo/advice-logo.jpg', cv2.IMREAD_UNCHANGED)

    # extract only bgr channels
    bgr = img[:, :, 0:3]

    # extract alpha channel
    a = img[:, :, 3]

    # blur alpha channel
    ab = cv2.GaussianBlur(a, (0,0), sigmaX=2, sigmaY=2, borderType = cv2.BORDER_DEFAULT)

    # stretch so that 255 -> 255 and 127.5 -> 0
    aa = skimage.exposure.rescale_intensity(ab, in_range=(127.5,255), out_range=(0,255))

    # replace alpha channel in input with new alpha channel
    out = img.copy()
    out[:, :, 3] = aa

    # save output
    cv2.imwrite('lena_circle_antialias.png', out)

    # Display various images to see the steps
    # NOTE: In and Out show heavy aliasing. This seems to be an artifact of imshow(), which did not display transparency for me. However, the saved image looks fine

    cv2.imshow('In',img)
    cv2.imshow('BGR', bgr)
    cv2.imshow('A', a)
    cv2.imshow('AB', ab)
    cv2.imshow('AA', aa)
    cv2.imshow('Out', out)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main() # Run script
    #inputQR = input('enter test: ')
    #QRregex(inputQR,mode='order')
    #putText('DH-12_19_Jun_2021.avi','Hello',180)
    #test_blur()
    
    
    