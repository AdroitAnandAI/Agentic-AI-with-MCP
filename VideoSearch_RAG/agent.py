import asyncio
import time
import os
import datetime
from perception import extract_perception
from memory import MemoryManager, MemoryItem
from decision import generate_plan
from action import execute_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
 # use this to connect to running server

import shutil
import sys

import re
import json
from pathlib import Path
from pywinauto.application import Application

def log(stage: str, msg: str):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

max_steps = 3

def open_video_and_frame(input_string):
    # Input string
    #input_string = "FINAL_ANSWER: [WW2 ended in 1945, C:\\EAG_Course\\Assignments\\7_RAG\\VideoSearch\\shared_data\\videos\\video1\\extracted_frame\\frame_29.jpg]"

    # Extracting '1' from 'video1'
    video_match = re.search(r"video(\d+)", input_string)
    video_number = int(video_match.group(1)) if video_match else None

    # Extracting '29' from 'frame_29'
    frame_match = re.search(r"frame_(\d+)", input_string)
    frame_number = int(frame_match.group(1)) if frame_match else None

    # Display results
    print("Video number:", video_number)  # Output: 1
    print("Frame number:", frame_number)  # Output: 29

    if video_number is not None and frame_number is not None:
        try:
            # Get the URL from mcp_rag.py's video_urls list
            from mcp_rag import video_urls
            if 1 <= video_number <= len(video_urls):
                url = video_urls[video_number - 1]
                
                # Read metadata file
                ROOT = Path(__file__).parent.resolve()
                METADATA_FILE = ROOT / "faiss_index" / "metadata.json"
                
                if METADATA_FILE.exists():
                    with open(METADATA_FILE, 'r') as f:
                        metadata = json.load(f)
                    
                    # Find the matching metadata entry
                    video_id = f"video{video_number}"
                    matching_entry = None
                    
                    # metadata is a list of lists, where each inner list contains metadata for a video
                    for video_metadata in metadata:
                        for entry in video_metadata:
                            if entry['video_id'] == video_id and entry['video_segment_id'] == frame_number:
                                matching_entry = entry
                                break
                        if matching_entry:
                            break
                    
                    if matching_entry:
                        # Convert milliseconds to seconds
                        mid_time_seconds = matching_entry['mid_time_ms'] / 1000
                        video_with_start_time = f"{url}&t={int(mid_time_seconds)}s"
                        
                        # Start Internet Explorer with the URL
                        app = Application().start(r"C:\Program Files\Internet Explorer\iexplore.exe " + video_with_start_time)
                        print(f"Opened video {video_number} in Internet Explorer at {mid_time_seconds} seconds: {video_with_start_time}")
                    else:
                        print(f"Could not find metadata for video {video_number}, frame {frame_number}")
                else:
                    print("Metadata file not found")
            else:
                print(f"Invalid video number. Please choose between 1 and {len(video_urls)}")
        except Exception as e:
            print(f"Failed to open video: {str(e)}")

async def main(user_input: str):
    try:
        print("[agent] Starting agent...")
        print(f"[agent] Current working directory: {os.getcwd()}")
        
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_rag.py"],
            cwd="C:/EAG_Course/Assignments/7_RAG/VideoSearch"
        )

        try:
            async with stdio_client(server_params) as (read, write):
                print("Connection established, creating session...")
                try:
                    async with ClientSession(read, write) as session:
                        print("[agent] Session created, initializing...")
 
                        try:
                            await session.initialize()
                            print("[agent] MCP session initialized")

                            # Your reasoning, planning, perception etc. would go here
                            tools = await session.list_tools()
                            print("Available tools:", [t.name for t in tools.tools])

                            # Get available tools
                            print("Requesting tool list...")
                            tools_result = await session.list_tools()
                            tools = tools_result.tools
                            tool_descriptions = "\n".join(
                                f"- {tool.name}: {getattr(tool, 'description', 'No description')}" 
                                for tool in tools
                            )

                            log("agent", f"{len(tools)} tools loaded")

                            memory = MemoryManager()
                            session_id = f"session-{int(time.time())}"
                            query = user_input  # Store original intent
                            step = 0

                            while step < max_steps:
                                log("loop", f"Step {step + 1} started")

                                perception = extract_perception(user_input)
                                log("perception", f"Intent: {perception.intent}, Tool hint: {perception.tool_hint}")

                                retrieved = memory.retrieve(query=user_input, top_k=3, session_filter=session_id)
                                log("memory", f"Retrieved {len(retrieved)} relevant memories")

                                plan = generate_plan(perception, retrieved, tool_descriptions=tool_descriptions)
                                log("plan", f"Plan generated: {plan}")

                                if plan.startswith("FINAL_ANSWER:"):
                                    log("agent", f"✅ FINAL RESULT: {plan}")
                                    open_video_and_frame(plan)
                                    break

                                try:
                                    result = await execute_tool(session, tools, plan)
                                    log("tool", f"{result.tool_name} returned: {result.result}")

                                    memory.add(MemoryItem(
                                        text=f"Tool call: {result.tool_name} with {result.arguments}, got: {result.result}",
                                        type="tool_output",
                                        tool_name=result.tool_name,
                                        user_query=user_input,
                                        tags=[result.tool_name],
                                        session_id=session_id
                                    ))

                                    user_input = f"Original task: {query}\nPrevious output: {result.result}\nWhat should I do next?"

                                except Exception as e:
                                    log("error", f"Tool execution failed: {e}")
                                    break

                                step += 1
                        except Exception as e:
                            print(f"[agent] Session initialization error: {str(e)}")
                except Exception as e:
                    print(f"[agent] Session creation error: {str(e)}")
        except Exception as e:
            print(f"[agent] Connection error: {str(e)}")
    except Exception as e:
        print(f"[agent] Overall error: {str(e)}")

    log("agent", "Agent session complete.")

if __name__ == "__main__":
    query = input("🧑 What do you want to solve today? → ")
    asyncio.run(main(query))


# Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.
# How much Anmol singh paid for his DLF apartment via Capbridge? 
# What do you know about Don Tapscott and Anthony Williams?
# What is the relationship between Gensol and Go-Auto?