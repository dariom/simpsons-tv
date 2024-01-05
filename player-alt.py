#!/usr/bin/env python3

import signal
import os
import sys
import RPi.GPIO as GPIO
import vlc
import time as time_ # Don't override time

class VideoSelector:
    def __init__(self, videoRoot, videoFileExtension):
        self._videoRoot = videoRoot
        self._videoFileExtension = videoFileExtension
        self._currentChannelIndex = 0
        self._currentVideoIndex = 0

        self._channels = []
        self._videos = []
        for videoRoot, channels, files in os.walk(self._videoRoot):
            for channel in channels:
                self._channels.append(channel)
            for file in files:
                filePath = os.path.join(videoRoot, file)
                if (os.path.exists(filePath) and filePath.lower().endswith(self._videoFileExtension)):
                    self._videos.append(filePath)
        self._channels.sort()
        if (len(self._channels) <= 0):
            print(f"Directory '{videoRoot}' does not contain any sub-directories to be used as a 'channel'.")
            quit()
        self._videos.sort()
        if (len(self._videos) <= 0):
            print(f"The directories within '{videoRoot}' do not contain any files with extension {self._videoFileExtension} to play.")
            quit()

    def get_current_channel(self):
        return self._channels[self._currentChannelIndex]
    
    def next_channel(self):
        self._currentChannelIndex += 1
        if (self._currentChannelIndex >= len(self._channels)):
            self._currentChannelIndex = 0

        # Find index of first video for the next channel
        channel = self.get_current_channel()
        channelPath = os.path.join(self._videoRoot, channel)
        for videoIndex in range(len(self._videos)):
            if (self._videos[videoIndex].startswith(channelPath)):
                return videoIndex
        
        return -1
    
    def get_videos(self):
        return self._videos


# Retrieves the number of milliseconds since power up
def get_timestamp():
    return int(round(time_.time() * 1_000))

# Stops the VLC player
def stop_vlc_player():
    global VlcMediaListPlayer
    VlcMediaListPlayer.stop()
    VlcMediaListPlayer.release()

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

# Right VCR button
# Long press (2 seconds or more) advances to next channel
# Short press (less than 2 seconds) advances to next video
def right_vcr_button_callback(channel):
    global RightButtonPressedStartTime
    global VlcMediaListPlayer
    global Videos

    if not GPIO.input(RIGHT_VCR_BUTTON_GPIO):
        # Start timer
        RightButtonPressedStartTime = get_timestamp()
    else:
        # Calculate time of right button release
        now = get_timestamp()
        if (now - RightButtonPressedStartTime >= 2_000):
            # Right button pressed and released for 2 seconds or more
            video_index = Videos.next_channel()
            VlcMediaListPlayer.play_item_at_index(video_index)
        else:
            VlcMediaListPlayer.next()

# Left VCR button
# Long press (1 seconds or more) rewind current video 10s
# Short press (less than 1 second) pause/resume playback
def left_vcr_button_callback(channel):
    global LeftButtonPressedStartTime
    global VlcMediaListPlayer

    if not GPIO.input(LEFT_VCR_BUTTON_GPIO):
        # Start timer
        LeftButtonPressedStartTime = get_timestamp()
    else:
        # Calculate time of left button release
        now = get_timestamp()

        if (now - LeftButtonPressedStartTime >= 1_000):
            # Left button pressed and released for 1 seconds or more
            mediaPlayer = VlcMediaListPlayer.get_media_player()
            mediaPlayer.set_time(mediaPlayer.get_time() - 10_000) # Rewind 10s
        else:
            VlcMediaListPlayer.pause() # Pause/Resume playback

SHUTDOWN_SIGNAL_GPIO  = 11
RIGHT_VCR_BUTTON_GPIO = 25
LEFT_VCR_BUTTON_GPIO  = 26

RightButtonPressedStartTime = 0
LeftButtonPressedStartTime = 0

Videos = VideoSelector('/home/pi/simpsonstv/videos/', '.mkv')
VlcInstance = vlc.Instance(['--quiet'])
VlcMediaListPlayer = vlc.MediaListPlayer()
VlcMediaList = VlcInstance.media_list_new(Videos.get_videos())
VlcMediaListPlayer.set_media_list(VlcMediaList)

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

    VlcMediaListPlayer.play()

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()