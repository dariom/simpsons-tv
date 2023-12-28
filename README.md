# The Simpsons TV project

This repository supports my modifications to [The Simpsons TV](https://withrow.io/simpsons-tv-build-guide) project originally created by Brandon Withrow and enhanced by D.J. Hatfield in his [larger 3.5" screen version](https://www.instructables.com/The-Simpsons-TV-35-Screen-Version/).

## What's different in this version?

I've primarily followed the [D.J. Hatfield's Instructables guide](https://www.instructables.com/The-Simpsons-TV-35-Screen-Version/) however his version is based on the "Buster" version of Raspberry Pi OS which is more difficult (not impossible though!) to find these days and impacts some of the software used in the build.

I used Raspberry Pi OS "Bullseye" in my version and as a result have had to make the following changes:

### VLC Player is used instead of OMX Player

This change requires alternative packages to be installed and D.J. Hatfield's `player.py` script to be modified to play videos using VLC.

## What I haven't fixed

### usbmount package is not available in Bullseye

The `usbmount` package has been removed from Raspberry Pi OS "Bullseye". This package was used to allow a USB device to be plugged into the Raspberry Pi to transfer video files. I'm not using this process to copy files to the Raspberry Pi as I simply transferred them over my local network.
