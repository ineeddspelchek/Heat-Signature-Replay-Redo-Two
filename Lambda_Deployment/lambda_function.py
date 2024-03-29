import boto3 
import pickle
from moviepy.editor import * #lets you edit videos

def lambda_handler(event, context):
    key = str(event)
    
    s3client = boto3.client("s3", region_name="us-east-1")
    
    
    rawfile = open("/tmp/raw.mp4", "wb")
    rawfile.write(s3client.get_object(Bucket="heatsigreplayraw", Key=key)["Body"].read())
    rawfile.close()
    s3client.delete_object(Bucket="heatsigreplayraw", Key=key)
    
    
    times = pickle.loads(s3client.get_object(Bucket="heatsigreplaytimes", Key=key)["Body"].read())
    s3client.delete_object(Bucket="heatsigreplaytimes", Key=key)
    
    return edit(times, key, s3client)

def edit(times, key, s3client): #create and edit raw footage from speed change timestamps
    pauseOffset = .05 #how much earlier to start pause to make sure its frames aren't included
    unpauseOffset = .05 #how much later to end unpause to make sure its frames aren't included


    inVid = VideoFileClip("/tmp/raw.mp4") #raw input clip

    clips = [] #list of clips to be combined
    for i in range(0, len(times)-1): #for all speed changes excluding the last
        if(times[i][1] != 0): #if not a pause
            if(i > 0 and times[i-1][1] == 0): #if a previous change exists and it is a pause, add a bit of an offset to remove any excess pause frames
                prevPause = True
            else: #if previous change is not a pause or none exists
                prevPause = False
                
            if(times[i+1][1] == 0): #if next speed change is a pause, cut earlier to remove any excess pause frames
                nextPause = True
            else: #if next change is not a pause
                nextPause = False
            
            if(prevPause and nextPause): #pause before and after current clip
                clipstart = min(times[i][0]+unpauseOffset, times[i+1][0]-pauseOffset)
                clipend = max(times[i+1][0]-pauseOffset, times[i][0]+unpauseOffset) 
            elif(prevPause): #pause only before current clip
                clipstart = min(times[i][0]+unpauseOffset, times[i+1][0]) 
                clipend = times[i+1][0]
            elif(nextPause): #pause only after current clip
                clipstart = times[i][0]
                clipend = max(times[i+1][0]-pauseOffset, times[i][0])
            else: #no pause before or after current clip
                clipstart = times[i][0]
                clipend = times[i+1][0]
                
            clipstart = max(clipstart, 0)
            clipend = max(clipend, 0)
                
            clipstart = min(clipstart, inVid.duration)
            clipend = min(clipend, inVid.duration)
            
            clip = inVid.subclip(clipstart, clipend)
            clip = clip.fx(vfx.speedx, 1/times[i][1])
            clips.append(clip)
            
    if(len(times) > 0): #if speed changes exist (should always since starting speed counts as a speed change)
        if(times[-1][0] < inVid.duration): #if start of last speed change doesn't exceed raw footage stop (could happen due to raw footage being slightly too fast)
            if(len(times) > 1 and times[-2][1] == 0): #if second to last speed change exists and is a pause, add a bit of an offset to remove any excess pause frames
                clip = inVid.subclip(min(times[-1][0]+unpauseOffset, inVid.duration), inVid.duration)
                clips.append(clip)
            elif(times[-1][1] != 0): #else if last speed change is not a pause
                clip = inVid.subclip(times[-1][0], inVid.duration)
                clip = clip.fx(vfx.speedx, 1/times[-1][1])
                clips.append(clip)
    else: #if no speed changes exist, return raw video as is
        clips.append(inVid)

    outVid = concatenate_videoclips(clips) #combine clips into one
    outVid.write_videofile("/tmp/out.mp4", fps=30) #output final mp4
    
    s3client.upload_file("/tmp/out.mp4", Bucket="heatsigreplayout", Key=key, Config=boto3.s3.transfer.TransferConfig())
    
    return "success"
