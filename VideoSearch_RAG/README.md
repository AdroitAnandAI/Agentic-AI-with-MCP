# Video Search with RAG and Vector Database

This project implements a Retrieval-Augmented Generation (RAG) system for video content, allowing users to search through video content using natural language queries. **The system processes YouTube videos, extracts frames and transcripts, and creates a searchable vector database using FAISS.**

 The system combines the power of vector databases (FAISS) with natural language processing to enable efficient search and retrieval of video content. **The agent will iteratively orchestrate between LLM and MCP tools to find out the relevant answer from the videos and gives the answer in textual format. In addition, the agent will open up the video and play from the exact location where the answer is found!**

## Project Structure

```
.
├── agent.py              # Main agent implementation for handling user queries
├── mcp_rag.py           # RAG implementation with MCP tools
├── utils.py             # Utility functions for video processing
├── process_videos.py    # Script for processing videos and creating FAISS index
├── download_process_video.py  # Script for downloading and processing videos
├── perception.py        # Perception module for understanding user intent
├── decision.py          # Decision making module
├── action.py            # Action execution module
├── memory.py            # Memory management for the agent
├── models.py            # Data models
├── faiss_index/         # Directory containing FAISS index and metadata
├── shared_data/         # Directory for storing processed videos and frames
└── documents/           # Directory for additional documents
```

## Key Features

- **Video Processing Pipeline**:
  - Downloads YouTube videos
  - Extracts frames at key timestamps
  - Processes video transcripts
  - Creates comprehensive metadata

- **Vector Database Integration**:
  - Uses FAISS for efficient similarity search
  - Maintains indexed embeddings of video content
  - Enables fast retrieval of relevant frames

- **Natural Language Interface**:
  - Accepts user queries in natural language
  - Processes and understands search intent
  - Returns relevant video segments and frames

- **Video Navigation**:
  - Opens videos at specific timestamps
  - Displays relevant frames
  - Provides context-aware search results

## Implementation Details

### 1. Video Processing
- Downloads videos using YouTube API
- Extracts frames at regular intervals
- Processes transcripts for text content
- Creates metadata for each frame including:
  - Timestamp information
  - Frame content description
  - Transcript segments

### 2. Vector Database
- Uses FAISS for efficient similarity search
- Indexes both visual and textual content
- Maintains embeddings for:
  - Frame content
  - Transcript segments
  - Combined visual-textual features

### 3. Search Interface
- Natural language query processing
- Multi-modal search capabilities
- Context-aware result ranking
- Interactive result display

## Usage Guide

1. **Initial Setup**:
   ```bash
   # Install required dependencies
   pip install -r requirements.txt
   ```

2. **Video Processing**:
   ```bash
   python mcp_rag.py
   ```
   This will:
   - Download specified YouTube videos
   - Extract and process frames
   **- Create FAISS index**
   - Generate metadata

**The conversion of video to transcript to embedding to vector index is a one time process. If the files are not modified then the processing will not be done again. To add more videos to the repository, just add the new URLs to the video_urls list in mcp_rag.py.** The code can be easily modified to take all the videos from an input folder to populate the video_urls list in mcp_rag.py.

3. **Running the System**:
   ```bash
   python agent.py
   ```
   The system will:
   - Accept natural language queries
   - Search through video content
   - Display relevant results
   - Enable video navigation

## Example Use Cases

1. **Educational Content Search**:
   **- "Find the part where they explain neural networks"**
   - "Show me examples of machine learning applications"
   - "What are the key concepts in deep learning?"

2. **Content Analysis**:
   **- Show me frames where machine learning is introduced**
   - Find details of mars rover mission from the videos
   - "Search for specific topics in the transcript"
   - "Locate key moments in the video"

## Technical Requirements

- Python 3.x
- FAISS for vector similarity search
- OpenCV for video processing
- PyWinAuto for video playback
- WebVTT for transcript processing
- Additional dependencies in `pyproject.toml`

## Performance Considerations

- Video processing time depends on:
  - Video length and quality
  - Number of frames to extract
  - Processing hardware capabilities
- Search performance optimized using:
  - FAISS indexing
  - Efficient metadata storage
  - Caching mechanisms

## Notes

- Requires stable internet connection for video downloads
- Processing time varies with video content
- FAISS index stored locally for quick access
- Metadata maintained in JSON format
- Supports batch processing of multiple videos 