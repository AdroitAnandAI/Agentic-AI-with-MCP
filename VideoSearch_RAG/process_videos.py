import os
from pathlib import Path
import json
import hashlib
import faiss
import numpy as np
from tqdm import tqdm
import cv2
import webvtt
from utils import (
    download_video, 
    get_transcript_vtt, 
    str2time, 
    maintain_aspect_ratio_resize,
    get_embedding
)

def process_videos():
    """Process videos and create FAISS index"""
    print("Indexing videos...")
    ROOT = Path(__file__).parent.resolve()
    VIDEO_PATH = ROOT / "shared_data" / "videos"
    INDEX_CACHE = ROOT / "faiss_index"
    INDEX_CACHE.mkdir(exist_ok=True)
    INDEX_FILE = INDEX_CACHE / "index.bin"
    METADATA_FILE = INDEX_CACHE / "metadata.json"
    CACHE_FILE = INDEX_CACHE / "video_index_cache.json"

    def file_hash(path):
        return hashlib.md5(Path(path).read_bytes()).hexdigest()

    CACHE_META = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
    index = faiss.read_index(str(INDEX_FILE)) if INDEX_FILE.exists() else None
    all_embeddings = []

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
                img_fpath = os.path.join(
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

    # List of video URLs to process
    video_urls = [
        "https://www.youtube.com/watch?v=HUqy-OQvVtI",
        "https://www.youtube.com/watch?v=H5VRs7-17Kg"
    ]

    # Process each video
    for video_idx, video_url in enumerate(video_urls):
        video_id = f"video{video_idx + 1}"
        video_dir = VIDEO_PATH / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing: {video_url}")
        try:
            # Download video
            video_filepath = download_video(video_url, str(video_dir))
            
            # Check if video has been processed
            fhash = file_hash(video_filepath)
            if video_filepath in CACHE_META and CACHE_META[video_filepath] == fhash:
                print(f"Skipping unchanged file: {video_filepath}")
                continue
            
            # Get transcript
            transcript_filepath = get_transcript_vtt(video_url, str(video_dir))
            
            # Create directory for extracted frames
            extracted_frames_path = video_dir / 'extracted_frame'
            extracted_frames_path.mkdir(parents=True, exist_ok=True)
            
            # Extract frames and metadata
            video_metadatas = extract_and_save_frames_and_metadata(
                video_filepath,
                transcript_filepath,
                str(extracted_frames_path),
                video_id
            )
            
            # Get embeddings for each frame's transcript
            embeddings_for_file = []
            for metadata in tqdm(video_metadatas, desc=f"Embedding {video_url}"):
                embedding = get_embedding(metadata['transcript'])
                embeddings_for_file.append(embedding)
            
            if embeddings_for_file:
                if index is None:
                    dim = len(embeddings_for_file[0])
                    index = faiss.IndexFlatL2(dim)
                index.add(np.stack(embeddings_for_file))
                metadata.extend(video_metadatas)
                CACHE_META[video_filepath] = fhash
                
        except Exception as e:
            print(f"Failed to process {video_url}: {e}")

    # Save cache, metadata and index
    CACHE_FILE.write_text(json.dumps(CACHE_META, indent=2))
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        print("Saved FAISS index and metadata")
    else:
        print("No new videos or updates to process.")

if __name__ == "__main__":
    process_videos() 