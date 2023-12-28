######################################################################################
# player.py
# Version:   1.0
# Author:    D.J. Hatfield
# Date:      2/21/2022
# Device:    Raspberry Pi Zero 2 W
# Purpose:   At startup, this script will start playing videos in the first subdirectory
#            under the "~/simpsonstv/videos/" specified by the "Directories" string array.
#            The next video in the same directory will automatically be played once the
#            existing video has completed playing.  All videos will be played in the current
#            specified directory and will loop around again once all are complete.
#
#
#            It also utilizes two "VCR" button inputs to implement the following features:
#             Right Button (GPIO 25):
#                -Quickly tap the button to select the next video in the current directory
#                -Press and hold the button for > 2 seconds to select the next "Channel"
#                 ("Channels" are just subdirectories under the ~/simpsonstv/videos/ directory and
#                  are specified in the "Directories" string array)
#             Left Button (GPIO 26):
#                -Quckly tap the button to pause or play the current video
#                -Press and hold the button for > 1 second to rewind current video by 10 seconds
#                 (continue holding to keep rewinding additional 10 seconds every second the button
#                  is pressed)
#             Press and hold BOTH the Right and Left buttons for > 5 seconds to shutdown the
#             OMXPlayer and exit this Python script and return to a command prompt.  NOTE: once
#             this Python script is terminated, the safe shutdown functionality will not work.
#             You will need to either restart this Python script to re-enable this functionality
#             or issue a "sudo shutdown now" command from a command prompt to safely shutdown the
#             Pi.
#
#             Additionally, this script monitors the Shutdown input (GPIO 11).  If this pin
#             is asserted (active LOW) for > 50mS, the Pi will be Shut down.
###########################################################################################

from omxplayer.player import OMXPlayer
from pathlib import Path
import os
import RPi.GPIO as GPIO
#import time as time_ - makes sure we don't override time
import time as time_
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Set GPIO 26 as input with pull-up
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Set GPIO 25 as input with pull-up
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Set GPIO 11 as input with pull-up

# Add/change your video subdirectories in the Directories string array
# These are the "Channels"
Directories = ["The Simpsons"]

#     <<<ROUTINES>>>
#-----------------------------------------------------------------------------------------------------------------
# millis(): Returns the number of milliseconds elapsed since power up.
def millis():
    return int(round(time_.time() * 1000))
#-----------------------------------------------------------------------------------------------------------------
# displayDirectoryVideo():  Displays the currently selected Video and Channel on the LCD
#                           Returns nothing
def displayDirectoryVideo():
    #Must specify "global" variables - otherwise, the routine would create its own unique copy
    # of these variables when they are used.
    global Root_Path
    global Current_Directory
    global Current_Video
    global VIDEO_PATH
    global PlayTimer
    global playNew
    os.system("clear")  #clear the LCD screen
    Current_Video = videos[Video_Pointer]  #Set current video to that specified by the Video_Pointer
    VIDEO_PATH = Path(Root_Path + Current_Directory + "/" + Current_Video)
    print("")
    print("")
    print("")
    print("  Channel: " + Current_Directory)  #Print the "Channel" (directory) on the LCD screen
    print("  " + Current_Video[0:len(Current_Video)-4])  #Print the video selected on the LCD screen
    PlayTimer = millis()
    playNew = True  #Trigger starting the play of the new video in 1.5 seconds
#-----------------------------------------------------------------------------------------------------------------
# nextVideo(): Select the next video by incrementing the Video_Pointer;  Loops around once the end is reached
#              Returns nothing
def nextVideo():
    #Must specify "global" variables - otherwise, the routine would create its own unique copy
    # of these variables when they are used.
    global Video_Pointer
    global videos
    global manualSelect
    global player
    manualSelect = True  #Set the flag to indicate the next video was manually selected
    player.quit()        #Stop the currently playing video - this kills the current OMXPlayer instance
    Video_Pointer += 1   # Increment Video_Pointer
    if(Video_Pointer > (len(videos)-1)):
      Video_Pointer = 0  #Loop Video_Pointer back around once end of videos is reached
    displayDirectoryVideo() #Display Channel and Selected Video on the LCD screen

#-----------------------------------------------------------------------------------------------------------------
# getVideos(): Update the videos string array with a list of videos in the currently selected channel (directory)
#              Returns nothing
def getVideos():
    #Must specify "global" variables - otherwise, the routine would create its own unique copy
    # of these variables when they are used.
    global videos
    global Current_Directory
    global Root_Path
    videos = []  #Clear out the videos string array
    for file in os.listdir(Root_Path + Current_Directory):  #Cycle through all files in the current directory and
        if file.lower().endswith('.mp4'):                   #add to videos string array if it is an mp4 video file
            videos.append(file)
    videos.sort() #Rearrange the videos in the videos array in alpha-numerical order

#-----------------------------------------------------------------------------------------------------------------
# switchDirectory(): Select the next channel (directory) in the Directories string array - also point to the first
#                    video in this newly selected channel.
#                    Returns nothing
def switchDirectory():
    #Must specify "global" variables - otherwise, the routine would create its own unique copy
    # of these variables when they are used.
    global Video_Pointer
    global Directory_Pointer
    global Current_Directory
    global Directories
    global manualSelect
    global player
    manualSelect=True   #Set the flag to indicate the next video was manually selected
    player.quit()       #Stop the currently playing video - this kills the current OMXPlayer instance
    Video_Pointer = 0   #Set video pointer to the first video in the newly specified channel
    Directory_Pointer +=1 #Increment the Channel Pointer
    if(Directory_Pointer > (len(Directories)-1)):
      Directory_Pointer = 0  #Loop the Channel pointer back around once end of channels is reached
    Current_Directory = Directories[Directory_Pointer]  #Set current channel specified by the Directory_Pointer
    getVideos()         #Identify all videos in the newly specified channel (directory)
    displayDirectoryVideo()  #Display Channel and Selected Video on the LCD screen
#-----------------------------------------------------------------------------------------------------------------
# autoPlayNext(): Executed when an instance of OMXPlayer exits.  It automatically starts playing the next video in
#                 the current channel if the last video played to completion.  It will not try to play a video if
#                 OMXPlayer was shutdown by the user manually (i.e. selecting through videos for the next video).
#                 In the case of a manual video selection, the video will be played in the main loop.
#                 Returns nothing
def autoPlayNext(code):
   #Must specify "global" variables - otherwise, the routine would create its own unique copy
   # of these variables when they are used.
   global Video_Pointer
   global videos
   global manualSelect
   global Video_Pointer
   if (manualSelect == True):  #If this routine was entered by the user manually selecting the next video,
     manualSelect = False      # clear the manualSelect flag and,
     return                    # return doing nothing else - the main loop will handle manual select operations
   Video_Pointer +=1 # If this routine was entered due to a video completing playback, increment the Video_Pointer
   if(Video_Pointer > (len(videos)-1)):  #Loop the video pointer back around once the end of videos is reached
     Video_Pointer = 0
   displayDirectoryVideo()     #Display Channel and Selected Video on the LCD screen

#--------------------------------------------------------------
#     <<<INITIALIZATION>>>     Executed only once at script start
os.system("clear")             #Clear the LCD screen
Video_Pointer = 0              #Set Video Pointer to point to the first video file in the current channel
oneShotNextVideo = False       #Controls incrementing video pointer only ONCE per right button press
oneShotNextDirectory = False   #Controls incrementing directory pointer only ONCE per extended right button press
manualSelect = False           #Indicates manual video select vs automatic selection of new video file
PlayTimer = 0                  #Delays playing next video (allows user to read Channel/Video selection on LCD
Root_Path = "/home/pi/simpsonstv/videos/"  #Path to this application's video channels(subdirectories)
Directory_Pointer = 0          #Set Channel (directory) pointer to first entry
Current_Directory = Directories[0] #Point current Channel to first directory in the Directories string array
getVideos()                    #populate videos string array with all video files located in the current channel
Current_Video = videos[0]      #Point current video to first video in the videos string array
VIDEO_PATH = Path(Root_Path + Current_Directory + "/" + Current_Video) #Set video path
player = OMXPlayer(VIDEO_PATH) #Start playing video specified by the video path
player.exitEvent += lambda _, exit_code: autoPlayNext(exit_code) #Set OMXPlayer exit event handler to call the
                                                                 # autoPlayNext() routine when OMXPlayer exits
Button1Timer = millis()        #Used to debounce VCR right button for select next video indication
Button2Timer = millis()        #Used to debounce VCR left button for select pause/play indication
ShutDownTimer = millis()       #Used to debounce Shutdown signal from the safe shutdown circuit
ExitPythonTimer = millis()     #Used to debounce the long press of BOTH left & right buttons to exit python script
seekTimer = millis()           #Used to debounce left button rewind long press
seekToggle = True              #Used to pulse a 10 second rewind for every second the left button is pressed
playNew = False                #When true, triggers playing a new video 1.5 seconds after a new video selection.
oneShotPlayPause = False       #Used to control executing a play or pause command only ONCE per left button press
skipPause = False              #Prevents executing a play/pause command during long (rewind) press of left button

#----------------------------------------------------------------------------------------------------------------
#     <<<MAIN>>>     Main program loop - continuously executes
while (True):

   input1 = GPIO.input(25)  #Read VCR right button input
   input2 = GPIO.input(26)  #Read VCR left button input
   ShutItDown = GPIO.input(11)  #Read Shutdown signal input
   #Check GPIO 25 and debounce high and low going pulses to see if
   #commanded to switch to next video in the current directory
   #or if commanded to go to the next channel (directory) if button pressed longer than 2 seconds
   if((input1 == True) and (oneShotNextVideo == False)):
     Button1Timer = millis()
     oneShotNextDirectory = False
   #Debounce right button (GPIO 25) going to the active state (LOW) for 100mS to select next video
   if((input1 == False)):
     temp = millis()
     if((temp - Button1Timer) >= 100):
        PlayTimer = millis()
        if(oneShotNextVideo == False):
          oneShotNextVideo = True
          nextVideo()
        oneShotCheckLow = True
     #Continue checking for button press > 2 seconds for change channel (directory)
     if((temp - Button1Timer) >= 2000):
        if(oneShotNextDirectory == False):
          switchDirectory()
          oneShotNextDirectory = True

   #Debounce right button (GPIO 25) going to the inactive state (HIGH) for 50mS
   if((input1 == True) and (oneShotNextVideo == True) and (oneShotCheckLow == True)):
      oneShotCheckLow = False
      Button1Timer = millis()
   if((input1 == True) and (oneShotNextVideo == True)):
      temp = millis()
      if((temp - Button1Timer) >= 50):
        oneShotNextVideo = False
   #-------------------------------------------------------------
   #Check GPIO 26 and debounce high and low going pulses to see if
   #commanded to switch to pause or rewind 10 seconds if pressed longer than 1 second
   if((input2 == True) and (oneShotPlayPause == False)):
     Button2Timer = millis()
     skipPause = False
   #Debounce left button (GPIO 26) going to the active state (LOW) for 100mS to toggle pause/play
   if((input2 == False)):
     temp = millis()
     if((temp - Button2Timer) >= 100):
       if((oneShotPlayPause == False) and (skipPause == False)):
         oneShotPlayPause = True
     #Continue checking for button press > 1 second for rewind
     if((temp - Button2Timer) >= 1000):
       if(seekToggle == True):
         try:                        #Implement exception handler (try: and except:) - prevents python script from
                                     # crashing if exception occurs during (try:) code
           player.seek(-10)          #Rewind video 10 seconds - causes exception if OMXPlayer has been terminated
           seekToggle = False
           seekTimer = millis()
           oneShotPlayPause = False
           skipPause = True
         except Exception as e:      #Exception handler - executes if exception occurs during above try:
           Nothing = 0               #  Exception code:does nothing-just catches exception/prevents Python crash
       #Continue rewinding 10 seconds for every 1 second the left button is pressed
       if((temp - seekTimer) >= 1000):
         seekToggle = True
         seekTimer = millis()

   #Debounce left button (GPIO 26) going to the inactive state (HIGH) for 50mS
   if((input2 == True) and (oneShotPlayPause == True)):
      temp = millis()
      if((temp - Button2Timer) >= 50):
        try:                         #Implement exception handler (try: and except:) - prevents python script from
                                     # crashing if exception occurs during (try:) code
          player.play_pause()        #Toggle video play/pause - causes exception if OMXPlayer has been terminated
          oneShotPlayPause = False
        except Exception as e:       #Exception handler - executes if exception occurs during above try:
          Nothing = 0                #  Exception code:does nothing-just catches exception/prevents Python crash

   #-------------------------------------------------------------
   #Check for special case of both VCR buttons pressed > 5 seconds (command to exit player.py Python script)
   if ((input1 == False) and (input2 == False)):
     temp = millis()
     if ((temp - ExitPythonTimer) >= 5000):
       player.quit()                 #Shut down OMXPlayer
       print("Exiting Python script")
       quit()                        #Exit player.py Python script
   else:
     ExitPythonTimer = millis()

   #-------------------------------------------------------------
   #Check GPIO pin 11 for signal to safetly shutdown Pi (active low)
   #  this signal is only debounced on assertion for 50mS
   temp = millis()
   if ((ShutItDown == False) and ((temp - ShutDownTimer) >= 50)):
     os.system("clear")              #Clear the LCD screen
     print("")
     print("")
     print("  Shutting Down...")     #Print "Shutting Down..." message on the LCD screen
     os.system("sudo shutdown -h now") #Shut down the Raspberry Pi - the safe shutdown circuit will monitor the
                                       # status LED signal and remove power once activity ceases
   if (ShutItDown == True):          #Reset ShutDown timer if ShutItDown signal deasserts before timer times out
     ShutDownTimer = millis()

   #-------------------------------------------------------------
   #Play next selection 1.5 seconds after last command to change video or directory
   #  This allows enough time for a user to read the channel (directory) and
   #  new video selected on the screen
   #  This is controlled by the playNew boolean variable.  When playNew is set, it
   #  triggers playing the new video 1.5 seconds later
   temp = millis()
   if((temp - PlayTimer) >= 1500 and (playNew == True)):
     player=OMXPlayer(VIDEO_PATH)   #Start playing video specified by the video path
     player.exitEvent = lambda _, exit_code: autoPlayNext(exit_code) #Set OMXPlayer exit event handler to call the
                                                                     # autoPlayNext() routine when OMXPlayer exits
     playNew = False                #Reset the playNew flag
     manualSelect = False           #Reset the manualSelect flag (indicates automatic play unless changed by user)
