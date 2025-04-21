from pathlib import Path
import os
from os import path as osp
import json
import cv2
import webvtt
# import whisper
# from moviepy.editor import VideoFileClip
from PIL import Image
import base64
from utils import download_video, get_transcript_vtt, str2time, maintain_aspect_ratio_resize

# List of video URLs to process
video_urls = [
    "https://www.youtube.com/watch?v=HUqy-OQvVtI",
    "https://www.youtube.com/watch?v=H5VRs7-17Kg"
]

# Base directory for all videos
base_dir = "./shared_data/videos"
Path(base_dir).mkdir(parents=True, exist_ok=True)

# Combined metadata for all videos
all_metadatas = []

def extract_and_save_frames_and_metadata(
        path_to_video, 
        path_to_transcript, 
        path_to_save_extracted_frames,
        video_id):
    
    # metadatas will store the metadata of all extracted frames
    metadatas = []

    # load video using cv2
    video = cv2.VideoCapture(path_to_video)
    # load transcript using webvtt
    trans = webvtt.read(path_to_transcript)
    
    # iterate transcript file
    # for each video segment specified in the transcript file
    for idx, transcript in enumerate(trans):
        # get the start time and end time in seconds
        start_time_ms = str2time(transcript.start)
        end_time_ms = str2time(transcript.end)
        # get the time in ms exactly 
        # in the middle of start time and end time
        mid_time_ms = (end_time_ms + start_time_ms) / 2
        # get the transcript, remove the next-line symbol
        text = transcript.text.replace("\n", ' ')
        # get frame at the middle time
        video.set(cv2.CAP_PROP_POS_MSEC, mid_time_ms)
        success, frame = video.read()
        if success:
            # if the frame is extracted successfully, resize it
            image = maintain_aspect_ratio_resize(frame, height=350)
            # save frame as JPEG file
            img_fname = f'frame_{idx}.jpg'
            img_fpath = osp.join(
                path_to_save_extracted_frames, img_fname
            )
            cv2.imwrite(img_fpath, image)

            # prepare the metadata
            metadata = {
                'extracted_frame_path': img_fpath,
                'transcript': text,
                'video_segment_id': idx,
                'video_path': path_to_video,
                'mid_time_ms': mid_time_ms,
                'video_id': video_id
            }
            metadatas.append(metadata)

        else:
            print(f"ERROR! Cannot extract frame: idx = {idx}")

    return metadatas

# Process each video
for video_idx, video_url in enumerate(video_urls):
    video_id = f"video{video_idx + 1}"
    video_dir = osp.join(base_dir, video_id)
    
    # Download video and transcript
    video_filepath = download_video(video_url, video_dir)
    transcript_filepath = get_transcript_vtt(video_url, video_dir)
    
    # Create directory for extracted frames
    extracted_frames_path = osp.join(video_dir, 'extracted_frame')
    Path(extracted_frames_path).mkdir(parents=True, exist_ok=True)
    
    # Extract frames and metadata
    video_metadatas = extract_and_save_frames_and_metadata(
        video_filepath,
        transcript_filepath,
        extracted_frames_path,
        video_id
    )
    
    # Append to combined metadata
    all_metadatas.extend(video_metadatas)

# Save combined metadata
metadata_filepath = osp.join(base_dir, 'metadatas.json')
with open(metadata_filepath, 'w') as outfile:
    json.dump(all_metadatas, outfile)