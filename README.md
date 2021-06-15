# OpenCV_Warehouse_Video_Record

This Project is to test the algorithm for Advice warehouse record using Raspberypi

#### Goal:
To make a system to record warehouse packing procedure by using Raspberry Pi and generate video output and store on the network

#### Specification:
1. Use webcam to record video
2. Use QR code to identify the name of the staff and Order number (2 Seperate variable)
3. The script run automatically when the Raspberry PI startup and waiting for input QR code
4. Video start (camera) recording after acquire both QR code
5. Have some way to end the video after finish packing process. Either ending by user or automate
6. Footage must be 3 minite long
7. In the footage there must be information of the order , time , logo of the company , ETC overlay the video
8. Post Video to the server by JSON format
9. Backup video for some time and delete to keep the storage
10. Have display to show status of the system
11. Optinal : Error proof if the user forgot to end recordind video
12. Optinal : Create a log file (CSV) to store the information


#### Detials
1. **Use webcam to record video**
  - Use OpenCV to capture the video
  - Store video in storage of raspberry PI
  - The video name must have meaning . For example: order number and date - time

2. **Use QR code to identify the name of the staff and Order number (2 Seperate variable)**
  - Use libray that compatible with OpenCV to detect barcode and translate into string
  - 2 String : 1 for Staff number , 2 for Order number

3. **The script run automatically when the Raspberry PI startup and waiting for input QR code**
  - After starting raspberry PI the script must be run automatically
  - Check if there is 2 input QR Code
  - Order of the input matter : Staff number first then order number
  - Show on the GUI staff number and order number
  - If there is more than 2 QR input , repeat the process again
  - To identify valid input for each QR we can use **Regular Expression**

4. **Video start (camera) recording after acquire both QR code**
  - After regrex identify valid input start recording

5. **Have some way to end the video after finish packing process. Either ending by user or automate**
  - At first we can use raw input to end the video manally or scan the QR code again
  - Or use PIR sensor to detect if the person are in the frame(need error checking)

6. **Footage must be 3 minite long**
  - Cut the last 3 minite of the video
  - if footage duration less than 3 minite. use the whole footage

8. **Post Video to the server by JSON format**
  - read the video to binary and convert to Base64 to reduce the length
  - store in JSON format
  - In the JSON format. There must be extra information about 
        - Name of the video
        - extension type of the file
        - Staff number
        - Order number
        - Date time of finishing process

9. **Backup video for some time and delete to keep the storage**
  - Crate a condition about the duration to keep file
  - Walk through storage directory and check if the file last longer than the time we accept then delete 
    these file
  - Comepare time can be done by find the gap between the file creation time and recent time
  - The process may run once after we start the hardware befoe execute the process or other condition

10. **Have display to show status of the system**
  - Show the display following list
     - Prompt the user to Scan QR Code
        - First ask for Staff ID (show if the value valid or not)
        - Then ask for order number (show if the value valid or not)
     - Show status that video in recording process
     - After ending video. Show the status
     - Also show the error if there are any

11. **Optinal : Error proof if the user forgot to end recordind video**
    - There may be the case if the user forgot to end the video and the next staff coming next

12. **Optinal : Create a log file (CSV) to store the information**
    - We can create a log file to store the information in case of we need to retrive information
      - Staff name and order number process today tie to date and time

###### Psedocode

- Start Program Automatically
- Check if it have valid folder structure to store video
    - Create folder if not available
- Check the video in store folder
- Delete video that have store more than 1 month
- **Prompt the user for ID QR Code**
- Check if the QR code is valid or go back to (**Prompt the user for ID QR Code**)
    - Get the information of ID number
    - **Prompt the user for Order number QR code**
    - Check if the Order no. QR code is valid or go back to (**Prompt the user for Order number QR code**)
        - Get the information of ID number   
    - Optinal : have a button to return to step 2 if user want to return to starting point
- Check if there are 2 valid QR code (ID and Order number) entering the system
    - Start capturing the video
    - After user finish the process. Stop video by sending signal (push button) (or Scan QR code again)
    - Get the information of Date,time,User ID, Order no
    - Cut the video into last 3 minute duration
    - Editing and apply information overlay to the video
    - Store video to the valid folder in the system
    - Stop camera
- Open latest video and convert to binary file
- Encode the information to Base64
- Create JSON packed and store video data
- **Send video to the Server**
    - Check if sending is success otherwise go back to (**Send video to the Server**)
 




