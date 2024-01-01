#!/usr/bin/env python3

import signal
import os
import sys
import RPi.GPIO as GPIO
import vlc
from pathlib import Path
import time as time_ # Don't override time

class VideoSelector:
    def __init__(self, videoRoot, videoFileExtension):
        self._videoRoot = videoRoot
        self._videoFileExtension = videoFileExtension
        self._currentChannelIndex = 0
        self._currentVideoIndex = 0

        self._channels = []
        for videoRoot, channels, files in os.walk(self._videoRoot):
            for channel in channels:
                self._channels.append(channel)
        self._channels.sort()
        if (len(self._channels) <= 0):
            print(f"Directory '{videoRoot}' does not contain any sub-directories to be used as a 'channels'.")
            quit()

        self._load_current_channel_videos()

    def _load_current_channel_videos(self):
        channel = self.get_current_channel()
        path = os.path.join(self._videoRoot, channel)

        self._videos = []
        for file in os.listdir(path):
            filePath = os.path.join(path, file)
            if (os.path.exists(filePath) and filePath.lower().endswith(self._videoFileExtension)):
                self._videos.append(file)
        self._videos.sort()
        if (len(self._videos) <= 0):
            print(f"Directory '{path}' does not contain any files with extension {self._videoFileExtension} to play back.")
            quit()

    def get_current_video_name(self):
        file = self._videos[self._currentVideoIndex]
        return file[0:(len(file) - len(self._videoFileExtension))] # Strip file extension from file

    def get_current_video(self):
        channel = self.get_current_channel()
        file = self._videos[self._currentVideoIndex]
        return os.path.join(self._videoRoot, channel, file)
    
    def get_current_channel(self):
        return self._channels[self._currentChannelIndex]
    
    def next_video(self):
        self._currentVideoIndex += 1
        if (self._currentVideoIndex >= len(self._videos)):
            self._currentVideoIndex = 0
            self.next_channel()
        
        return self.get_current_video()
    
    def next_channel(self):
        self._currentChannelIndex += 1
        if (self._currentChannelIndex >= len(self._channels)):
            self._currentChannelIndex = 0
        
        self._load_current_channel_videos()
        self._currentVideoIndex = 0
        return self.get_current_channel()


# Retrieves the number of milliseconds since power up
def get_timestamp():
    return int(round(time_.time() * 1000))

# Stops the VLC player
def stop_vlc_player():
    global VlcPlayer
    VlcPlayer.stop()

# Helper routine to play the current video
def play_vlc_current_video():
    global Videos
    global VlcInstance
    global VlcPlayer
    stop_vlc_player()
    display_current_video(Videos.get_current_channel(), Videos.get_current_video_name())
    media = VlcInstance.media_new_path(Videos.get_current_video())
    VlcPlayer.set_media(media)
    VlcPlayer.play()

# Handles SIGINT signal (CTRL+C) and exits the script
def signal_handler(sig, frame):
    stop_vlc_player()
    GPIO.cleanup()
    sys.exit(0)

# Shutdown the Raspberry Pi
def shutdown_signal_callback(channel):
    if GPIO.input(SHUTDOWN_SIGNAL_GPIO):
        # TODO: This should work, but I haven't tested it as I haven't used the safe shutdown circuit
        stop_vlc_player()
        GPIO.cleanup()
        os.system("clear")
        print("")
        print("")
        print("Shutting Down...")
        os.system("sudo shutdown -h now")

# Displays the current channel and video name on screen
def display_current_video(channel, video):
    os.system("clear")
    print("")
    print("")
    print("")
    print(f"{channel}")
    print("")
    print(f"{video}")
    print("")
    print("")
    print("")
    time_.sleep(1.5)

# Right VCR button
# Long press (2 seconds or more) advances to next channel
# Short press (less than 2 seconds) advances to next video
def right_vcr_button_callback(channel):
    global RightButtonPressedStartTime
    global Videos

    if not GPIO.input(RIGHT_VCR_BUTTON_GPIO):
        # Start timer
        RightButtonPressedStartTime = get_timestamp()
    else:
        # Calculate time of right button release
        now = get_timestamp()
        if (now - RightButtonPressedStartTime >= 2000):
            # Right button pressed and released for 2 seconds or more
            Videos.next_channel()
        else:
            Videos.next_video()
        play_vlc_current_video()

# Left VCR button
# Long press (1 seconds or more) rewind current video 10s
# Short press (less than 1 second) pause/resume playback
def left_vcr_button_callback(channel):
    global LeftButtonPressedStartTime
    global Videos
    global VlcPlayer

    if not GPIO.input(LEFT_VCR_BUTTON_GPIO):
        # Start timer
        LeftButtonPressedStartTime = get_timestamp()
    else:
        # Calculate time of left button release
        now = get_timestamp()

        if (now - LeftButtonPressedStartTime >= 1000):
            # Left button pressed and released for 1 seconds or more
            #VlcPlayer.set_time(VlcPlayer.get_time() - 10000) # Rewind 10s
            #TODO restore the previous line
            VlcPlayer.set_time(23 * 60000) # Forward 21mins
        else:
            VlcPlayer.pause() # Pause/Resume playback

# Reached end of video, advance to next
def end_of_video_reached_callback(event):
    global Videos
    Videos.next_video()
    play_vlc_current_video()


SHUTDOWN_SIGNAL_GPIO  = 11
RIGHT_VCR_BUTTON_GPIO = 25
LEFT_VCR_BUTTON_GPIO  = 26

RightButtonPressedStartTime = 0
LeftButtonPressedStartTime = 0
Videos = VideoSelector('/home/pi/simpsonstv/videos/', '.mkv')
VlcInstance = vlc.Instance(['--quiet', '--file-logging', '--logfile=/home/pi/simpsonstv/vlc.log','--logmode=text', '--log-verbose=3'])
VlcPlayer = VlcInstance.media_player_new()

# Set up VLC media player end reached callback
VlcEventManager = VlcPlayer.event_manager()
VlcEventManager.event_attach(vlc.EventType.MediaPlayerEndReached, end_of_video_reached_callback)

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)

    # Setup shutdown button callback
    GPIO.setup(SHUTDOWN_SIGNAL_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(SHUTDOWN_SIGNAL_GPIO, GPIO.BOTH, 
            callback=shutdown_signal_callback, bouncetime=30)

    # Setup right VCR button callback
    GPIO.setup(RIGHT_VCR_BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(RIGHT_VCR_BUTTON_GPIO, GPIO.BOTH, 
            callback=right_vcr_button_callback, bouncetime=30)

    # Setup left VCR button callback
    GPIO.setup(LEFT_VCR_BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(LEFT_VCR_BUTTON_GPIO, GPIO.BOTH, 
            callback=left_vcr_button_callback, bouncetime=30)
    
    play_vlc_current_video()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()