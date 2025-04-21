from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import os
import json
import faiss
import numpy as np
from pathlib import Path
import requests
from markitdown import MarkItDown
import time
import cv2
import webvtt
from models import AddInput, AddOutput, SqrtInput, SqrtOutput, StringsToIntsInput, StringsToIntsOutput, ExpSumInput, ExpSumOutput
from PIL import Image as PILImage
from tqdm import tqdm
import hashlib
from utils import download_video, get_transcript_vtt, str2time, maintain_aspect_ratio_resize
# from process_videos import process_videos


mcp = FastMCP("Calculator")

EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 40
ROOT = Path(__file__).parent.resolve()


# List of video URLs to process
video_urls = [
    "https://www.youtube.com/watch?v=HUqy-OQvVtI",
    "https://www.youtube.com/watch?v=H5VRs7-17Kg",
    # "https://www.youtube.com/watch?v=Jyiw6KkedDY",
    # "https://www.youtube.com/watch?v=6qS83wD29PY"
]

def get_embedding(text: str) -> np.ndarray:
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    for i in range(0, len(words), size - overlap):
        yield " ".join(words[i:i+size])

def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()

# @mcp.tool()
# def search_documents(query: str) -> list[str]:
#     """Search for relevant content from uploaded documents."""
#     ensure_faiss_ready()
#     mcp_log("SEARCH", f"Query: {query}")
#     try:
#         index = faiss.read_index(str(ROOT / "faiss_index" / "index.bin"))
#         metadata = json.loads((ROOT / "faiss_index" / "metadata.json").read_text())
#         query_vec = get_embedding(query).reshape(1, -1)
#         D, I = index.search(query_vec, k=5)
#         results = []
#         for idx in I[0]:
#             data = metadata[idx]
#             results.append(f"{data['chunk']}\n[Source: {data['doc']}, ID: {data['chunk_id']}]")
#         return results
#     except Exception as e:
#         return [f"ERROR: Failed to search: {str(e)}"]

@mcp.tool()
def search_videos(query: str) -> list[str]:
    """Search for factual content from processed videos."""
    mcp_log("SEARCH", f"Video Query: {query}")
    try:
        # Load the FAISS index and metadata
        index = faiss.read_index(str(ROOT / "faiss_index" / "index.bin"))
        all_metadata = json.loads((ROOT / "faiss_index" / "metadata.json").read_text())
        
        # Get embedding for the query
        query_vec = get_embedding(query).reshape(1, -1)
        
        # Search the index
        D, I = index.search(query_vec, k=5)
        
        # Process results
        results = []
        for idx in I[0]:
            # Since all_metadata is a list of video metadata lists, we need to find the correct video and frame
            video_idx = 0
            frame_idx = idx
            while video_idx < len(all_metadata) and frame_idx >= len(all_metadata[video_idx]):
                frame_idx -= len(all_metadata[video_idx])
                video_idx += 1
            
            if video_idx < len(all_metadata) and frame_idx < len(all_metadata[video_idx]):
                frame_data = all_metadata[video_idx][frame_idx]
                results.append(
                    f"Transcript: {frame_data['transcript']}\n"
                    f"Video: {frame_data['video_id']}\n"
                    f"Time: {frame_data['mid_time_ms']/1000:.2f}s\n"
                    f"Frame: {frame_data['extracted_frame_path']}"
                )
        
        return results if results else ["No matching video segments found."]
    except Exception as e:
        return [f"ERROR: Failed to search videos: {str(e)}"]

@mcp.tool()
def add(input: AddInput) -> AddOutput:
    print("CALLED: add(AddInput) -> AddOutput")
    return AddOutput(result=input.a + input.b)

@mcp.tool()
def sqrt(input: SqrtInput) -> SqrtOutput:
    """Square root of a number"""
    print("CALLED: sqrt(SqrtInput) -> SqrtOutput")
    return SqrtOutput(result=input.a ** 0.5)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)


# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(input: StringsToIntsInput) -> StringsToIntsOutput:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(StringsToIntsInput) -> StringsToIntsOutput")
    ascii_values = [ord(char) for char in input.string]
    return StringsToIntsOutput(ascii_values=ascii_values)

@mcp.tool()
def int_list_to_exponential_sum(input: ExpSumInput) -> ExpSumOutput:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(ExpSumInput) -> ExpSumOutput")
    result = sum(math.exp(i) for i in input.int_list)
    return ExpSumOutput(result=result)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

def process_documents():
    """Process documents and create FAISS index"""
    mcp_log("INFO", "Indexing documents with MarkItDown...")
    ROOT = Path(__file__).parent.resolve()
    DOC_PATH = ROOT / "documents"
    INDEX_CACHE = ROOT / "faiss_index"
    INDEX_CACHE.mkdir(exist_ok=True)
    INDEX_FILE = INDEX_CACHE / "index.bin"
    METADATA_FILE = INDEX_CACHE / "metadata.json"
    CACHE_FILE = INDEX_CACHE / "doc_index_cache.json"

    def file_hash(path):
        return hashlib.md5(Path(path).read_bytes()).hexdigest()

    CACHE_META = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
    index = faiss.read_index(str(INDEX_FILE)) if INDEX_FILE.exists() else None
    all_embeddings = []
    converter = MarkItDown()

    for file in DOC_PATH.glob("*.*"):
        fhash = file_hash(file)
        if file.name in CACHE_META and CACHE_META[file.name] == fhash:
            mcp_log("SKIP", f"Skipping unchanged file: {file.name}")
            continue

        mcp_log("PROC", f"Processing: {file.name}")
        try:
            result = converter.convert(str(file))
            markdown = result.text_content
            chunks = list(chunk_text(markdown))
            embeddings_for_file = []
            new_metadata = []
            for i, chunk in enumerate(tqdm(chunks, desc=f"Embedding {file.name}")):
                embedding = get_embedding(chunk)
                embeddings_for_file.append(embedding)
                new_metadata.append({"doc": file.name, "chunk": chunk, "chunk_id": f"{file.stem}_{i}"})
            if embeddings_for_file:
                if index is None:
                    dim = len(embeddings_for_file[0])
                    index = faiss.IndexFlatL2(dim)
                index.add(np.stack(embeddings_for_file))
                metadata.extend(new_metadata)
            CACHE_META[file.name] = fhash
        except Exception as e:
            mcp_log("ERROR", f"Failed to process {file.name}: {e}")

    CACHE_FILE.write_text(json.dumps(CACHE_META, indent=2))
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        mcp_log("SUCCESS", "Saved FAISS index and metadata")
    else:
        mcp_log("WARN", "No new documents or updates to process.")

def ensure_faiss_ready():
    from pathlib import Path
    index_path = ROOT / "faiss_index" / "index.bin"
    meta_path = ROOT / "faiss_index" / "metadata.json"
    if not (index_path.exists() and meta_path.exists()):
        mcp_log("INFO", "Index not found — running process_documents()...")
        process_documents()
    else:
        mcp_log("INFO", "Index already exists. Skipping regeneration.")



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

    # all_metadata = []
    CACHE_META = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    all_metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
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
                frame_metadata = {
                    'extracted_frame_path': img_fpath,
                    'transcript': text,
                    'video_segment_id': idx,
                    'video_path': path_to_video,
                    'mid_time_ms': mid_time_ms,
                    'video_id': video_id
                }
                metadatas.append(frame_metadata)

            else:
                print(f"ERROR! Cannot extract frame: idx = {idx}")

        return metadatas


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
            for frame_metadata in tqdm(video_metadatas, desc=f"Embedding {video_url}"):
                embedding = get_embedding(frame_metadata['transcript'])
                embeddings_for_file.append(embedding)
            
            if embeddings_for_file:
                if index is None:
                    dim = len(embeddings_for_file[0])
                    index = faiss.IndexFlatL2(dim)
                index.add(np.stack(embeddings_for_file))
                print(f"all_metadata = {all_metadata}")
                all_metadata.append(video_metadatas)
                CACHE_META[video_filepath] = fhash
                
        except Exception as e:
            print(f"Failed to process {video_url}: {e}")

    # Save cache, metadata and index
    CACHE_FILE.write_text(json.dumps(CACHE_META, indent=2))
    METADATA_FILE.write_text(json.dumps(all_metadata, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        print("Saved FAISS index and metadata")
    else:
        print("No new videos or updates to process.")


if __name__ == "__main__":
    print("STARTING THE SERVER AT AMAZING LOCATION")    
    
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run() # Run without transport for dev server
    else:
        # Start the server in a separate thread
        import threading
        server_thread = threading.Thread(target=lambda: mcp.run(transport="stdio"))
        server_thread.daemon = True
        server_thread.start()
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Process documents after server is running
        # process_documents()
        process_videos()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
