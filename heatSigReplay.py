import datetime
import time #lets you get current time
from datetime import datetime #lets you get a different current time (easier to access month, day, year, hour, minute, and second)

#memory only read, never written
from ReadWriteMemory import ReadWriteMemory
from process_interface import ProcessInterface 
from ctypes import *
import pymem

import cv2
import numpy as np
import pyautogui
import mss
import win32gui
import pywintypes

from pynput import keyboard
import threading

from moviepy.editor import * #lets you edit videos

import boto3
import random
import botocore
import pickle

lambdaclient = boto3.client(service_name='lambda', 
                            region_name="us-east-1", 
                            aws_access_key_id="", 
                            aws_secret_access_key="")
s3client = boto3.Session().client(service_name="s3", 
                                  region_name="us-east-1", 
                                  aws_access_key_id="", 
                                  aws_secret_access_key="",
                                  config=botocore.config.Config(max_pool_connections=20, connect_timeout=100000, read_timeout=10000))
s3t = boto3.s3.transfer.create_transfer_manager(s3client, config=boto3.s3.transfer.TransferConfig(max_concurrency=40, multipart_threshold=10000000, multipart_chunksize=10000000))

if(not os.path.exists("hsConfig.txt")):
    print("hsConfig.txt not found. Creating file.")
    config = open("hsConfig.txt", "w")
    config.writelines(["(True to use one key to toggle recording or False to have one for start one for stop) RecordingToggle=True\n",
                       "(Key to begin or toggle recording) Start/ToggleRecordingKey=g\n",
                       "(Key to stop recording) StopRecordingKey=h\n",
                       "(True to not slow down fastmo in clips or False to slow them) KeepFastMo=True\n"])
    config.close()

input("Press Enter in this window once you have configured hsConfig.txt how you want it.")

print("\n")

config = open("hsConfig.txt", "r")
lines = config.readlines()

recordToggle = lines[0][-6].upper() != "F" #True if you only want one key to toggle recording; False if you want separate record and stop record buttons
recordKey1 = keyboard.KeyCode.from_char(lines[1][-2].lower()) #record button or toggle
recordKey2 = keyboard.KeyCode.from_char(lines[2][-2].lower()) #stop record button
#   *example keybinds: keyboard.KeyCode.from_char('a'), keyboard.Key.space, keyboard.Key.alt_l, keyboard.Key.ctrl_r
keepFastMo = lines[3][-6].upper() != "F" #when True, doesn't slow down fast mo (if false, those segments go down to 5 fps)


###################################

generalOffset = -.08 #how much earlier to set timestamps to account for delay in fetching timescale variable

######################################################################################################################
    
if(recordToggle):
    print("Press " + recordKey1.char + " to start/stop recording.")
else:
    print("Press " + recordKey1.char + " to start recording. \nPress " + recordKey2.char + " to stop recording.")

######################################################################################################################
#adapted from the following with author's permission:
#https://youtu.be/x4WE3mSJoRA
#https://youtu.be/OEgvqDbdfQI
#https://youtu.be/Pv0wx4uHRfM

base_address = pymem.Pymem(process_name="Heat_Signature.exe").base_address
static_address_offset = 0x0453D610
pointer_static_address = base_address + static_address_offset
offsets = [0x60, 0x10, 0x3C4, 0x1B0]

rwm = ReadWriteMemory()
process = rwm.get_process_by_name("Heat_Signature.exe")
process.open()
my_pointer = process.get_pointer(pointer_static_address, offsets=offsets)

process2 = ProcessInterface()
process2.open("Heat_Signature.exe")

######################################################################################################################

def record(key): #handle record presses
    global recordToggle, recording
    
    if(recordToggle): #if set to toggle
        if(key == recordKey1): #if record toggle pressed
            recording = not recording
            if(recording):
                print("RECORDING")
            else:
                print("NOT RECORDING")
    else: #if not toggling
        if(key == recordKey1): #if record key pressed
            recording = True
            print("RECORDING")
        elif(key == recordKey2): #if stop record key pressed
            recording = False
            print("NOT RECORDING")


recording = False 
listener = keyboard.Listener(on_press=record) #set up keyboard listener
listener.start() #starts keyboard listener
recorder = mss.mss() #screenshot taker set up

def main():
    global recording
    
    recording = False
    firstbbox = -1

    while(True): #while code runs
        #reset/set values
        readyToEdit = False #if raw footage is ready to put together and edit
        baseTime = time.time() #time recording began
        currFrame = 0 #current frame
        shots = [] #list of shots from recorder
        prevSpeed = -1 #last recorded speed
        currSpeed = c_double.from_buffer(process2.read_memory(my_pointer, buffer_size=8)).value #current speed; also adapted from the 3 youtube videos
        times = [] #entries consisting of [timescale change start time, new timescale]
        
        state = 0 #0-Paused, 1-Slow, 2-Normal, 3-Fast
        if(currSpeed == 0): #if starting paused
            state = 0
            times.append([time.time()-baseTime, 0])
        elif(currSpeed < .6): #if starting slow
            state = 1
            times.append([time.time()-baseTime, .2])
        elif(currSpeed >= .6 and (currSpeed <= 1 or keepFastMo)): #if starting normal (or fast, but ignoring it)
            state = 2
            times.append([time.time()-baseTime, 1])
        else: #if starting fast (and not ignoring it)
            state = 3
            times.append([time.time()-baseTime, 6])
        
        while(recording):
            if(time.time() - baseTime >= currFrame/30): #if ready for next screenshot (1/30 of a second has passed since last one)
                prevSpeed = currSpeed #last current speed is new previous speed
                currSpeed = c_double.from_buffer(process2.read_memory(my_pointer, buffer_size=8)).value #new current speed accessed; also adapted from the 3 youtube videos
                if(currSpeed != prevSpeed): #if speed has changed
                    if(currSpeed == 0 and state != 0): #if now paused but not yet considered paused
                        state = 0
                        times.append([time.time()-baseTime+generalOffset, 0])
                    elif(currSpeed < .6 and state != 1): #if now slow but not yet considered slow
                        state = 1
                        times.append([time.time()-baseTime+generalOffset, .2])
                    elif(currSpeed >= .6 and currSpeed <= 1 and state != 2): #if now normal but not yet considered normal
                        state = 2
                        times.append([time.time()-baseTime+generalOffset, 1])
                    elif(currSpeed > 1 and state != 3 and not keepFastMo): #if now fast but not yet considered fast (and not ignoring fast)
                        state = 3
                        times.append([time.time()-baseTime+generalOffset, 6])
                        
                ###########################################################################################################
                # from https://stackoverflow.com/questions/3260559/how-to-get-a-window-or-fullscreen-screenshot-without-pil
                try:
                    toplist, winlist = [], []
                    def enum_cb(hwnd, results):
                        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
                    win32gui.EnumWindows(enum_cb, toplist)

                    hwnd = [(hwnd, title) for hwnd, title in winlist if 'Heat Signature' == title][0][0]

                    win32gui.SetForegroundWindow(hwnd)
                    bbox = win32gui.GetWindowRect(hwnd)
                    if(firstbbox == -1): #if first bounds haven't been set, set them to current bounds
                        firstbbox = bbox
                except pywintypes.error: #if window is closed
                    bbox = -1
                ###########################################################################################################

                if(bbox != firstbbox): #if bounds are not the same as the first bounds, just reuse the last shot and consider yourself currently paused until it is resolved
                    state = 0
                    times.append([time.time()-baseTime+generalOffset, 0])
                    try:
                        shots.append(shots[-1])
                    except IndexError:
                        recording = False
                        print("GAME WINDOW NOT OPEN\nNOT RECORDING")
                else:
                    try:
                        shots.append(pyautogui.screenshot(region=bbox)) #take a screenshot and store it
                    except TypeError:
                        recording = False
                        print("GAME WINDOW NOT OPEN\nNOT RECORDING")
                currFrame += 1 #increment current frame
            readyToEdit = True
            
        if(readyToEdit and len(shots) > 0): #if raw footage ready to put together and edit
            editTimer = threading.Timer(0, edit, args=[times, shots]) #set up edit
            editTimer.start() #start edit

def edit(times, shots):
    print("Processing Footage...")
    
    now = datetime.now() #current time
    timeStr = str(now.month) + "-" + str(now.day) + "-" + str(now.year) + "_" + str(now.hour) + "," + str(now.minute) + "," + str(now.second) #file identifier
    
    #from https://www.thepythoncode.com/article/make-screen-recorder-python 
    raw = cv2.VideoWriter(timeStr+"_raw.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 30, tuple(pyautogui.size()))
    
    for i in range(0, len(shots)):
        frame = np.array(shots[i])
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        raw.write(frame)
    raw.release()
    
    key = random.randint(0, 999999999999)
    tagset = s3client.get_bucket_tagging(Bucket="heatsigreplayraw")["TagSet"]
    keyset = [tag.get("Key") for tag in tagset]
    while(True): #roll keys until you get an unused one
        if(not key in keyset):
            break
        else:
            key = random.randint(0, 999999999999)
    
    print(str(key) + ": UPLOADING FOOTAGE")
    ##############################################################################################################
    # from https://stackoverflow.com/questions/56639630/how-can-i-increase-my-aws-s3-upload-speed-when-using-boto3
    
    size = os.stat(timeStr+"_raw.mp4").st_size
    transferred = 0
    
    def progress_update(transferredOnce):        
        nonlocal transferred
        
        transferred += transferredOnce
        print(str(key) + ": " + format(transferred/size, ".1%") + " UPLOADED")
    
    s3client.upload_file(Filename=timeStr+"_raw.mp4",
            Bucket="heatsigreplayraw", 
            Key=str(key),
            Callback=progress_update,
            Config=boto3.s3.transfer.TransferConfig(max_concurrency=40, multipart_threshold=10000000, multipart_chunksize=10000000))
    ##############################################################################################################
    s3client.put_object(Body=pickle.dumps(times), 
                            Bucket="heatsigreplaytimes",
                            Key=str(key))
    print(str(key) + ": UPLOAD DONE; EDITING IN CLOUD")
    
    response = lambdaclient.invoke(FunctionName="arn:aws:lambda:us-east-1:948974275354:function:heatSigReplayProcessing", 
                                    Payload=str(key))
    print(str(key) + ": EDIT IN CLOUD DONE; DOWNLOADING FOOTAGE")
    
    back = response["Payload"].read()
    
    if(str(back) == "b\'\"success\"\'"):
        out = open(timeStr+"_out.mp4", "wb")
        out.write(s3client.get_object(Bucket="heatsigreplayout", Key=str(key))["Body"].read())
        out.close()
        s3client.delete_object(Bucket="heatsigreplayout", Key=str(key))
        print(str(key) + ": DOWNLOAD DONE")
    else:
        print(str(key) + ": EDIT/DOWNLOAD FAILED")

main() #run main