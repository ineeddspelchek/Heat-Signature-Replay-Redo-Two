# IMPORTANT Disclaimer
SCREENSHOTS TAKEN WHILE RUNNING THIS PROGRAM ARE SENT ONLINE TO AMAZON WEB SERVICE CLOUD STORAGE.

This program is moreso a demonstration of my knowledge of the basics of AWS than it is actually meant for use. More than likely, you would do just as well running [my earlier, entirely local/offline version](https://github.com/ineeddspelchek/Heat-Signature-Replay-Redo) of the same program.

That being said, if you do wish to run this program regardless, know the following:
* All data sent by this program to the cloud is deleted as soon as it is done being used. Even if the progam halts before it is able to trigger deletion, I've set up AWS to delete any stored file 1 day after its creation.
* Though the program logs keystrokes from up to 2 keys (the start/stop recording keys), this is stored entirely locally and will not be sent to the cloud. The same goes for computer memory being read.
* Only screenshots are sent to the cloud and these should only be screenshots of the Heat Signature game window.
* I *do* have access to any files sent to the cloud up until the point at which they are deleted, but no one else will be given access and I will not access any files that were not created by me.

# Heat-Signature-Replay-Redo-Two
Online version of my Heat Signature Replay Redo program to record and edit Heat Signature clips into realtime speed 

## How It Works
1. When you start a recording, the program will read the game's memory to keep track of the in-game speed. At the same time, it will begin taking screenshots of gameplay at 30 fps.
2. Once you stop the recording, the screenshots are compiled into a "raw" .mp4 file that will save to the `heatSigReplay` folder.
3. This .mp4 along with a list of speed change timestamps are both uploaded separately to two AWS S3 buckets.
4. After the upload is complete, the program will notify an AWS Lambda function of that fact.
5. The Lambda function will then edit the footage into an `out` .mp4 which is uploaded to a third S3 bucket.
6. The Lambda function then notifies this program that is has completed the edit and successfully put out the file.
7. This program will finally download the file from that S3 bucket into the `heatSigReplay` folder.

# How To
1. Download the latest release.
2. Extract `heatSigReplay.zip`
3. Whitelist `heatSigReplay.exe` on Windows Defender. 
4. Run Heat Signature **in full screen**.
5. Run `heatSigReplay.exe`.
6. Wait a few seconds for text to appear in the window and then follow its directions.
7. Play.
8. Close the program after the last `out.mp4` clip is downloaded (you can quit earlier, but you'll lose any out recordings that haven't completed).

## Credits
Much of this comes thanks to two people:
* Random Davis (www.youtube.com/user/r2blend) for his interface for reading memory with Python, and
* @DurryQuill from the Suspicious Developments Discord who found the in-game variable address that makes this entire program possible to begin with
