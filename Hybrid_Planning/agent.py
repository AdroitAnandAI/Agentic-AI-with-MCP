# agent.py

import asyncio
import yaml
from core.loop import AgentLoop
from core.session import MultiMCP
from core.context import MemoryItem, AgentContext
import datetime
from pathlib import Path
import json
import re

def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

async def main():
    print("🧠 Cortex-R Agent Ready")
    current_session = None

    with open("config/profiles.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers_list = profile.get("mcp_servers", [])
        mcp_servers = {server["id"]: server for server in mcp_servers_list}

    multi_mcp = MultiMCP(server_configs=list(mcp_servers.values()))
    await multi_mcp.initialize()
    
    try:
        while True:
            user_input = input("🧑 What do you want to solve today? → ")
            if user_input.lower() == 'exit':
                break
            if user_input.lower() == 'new':
                current_session = None
                continue

            while True:
                context = AgentContext(
                    user_input=user_input,
                    session_id=current_session,
                    dispatcher=multi_mcp,
                    mcp_server_descriptions=mcp_servers,
                )
                agent = AgentLoop(context)
                if not current_session:
                    current_session = context.session_id

                result = await agent.run()

                if isinstance(result, dict):
                    answer = result["result"]
                    if "FINAL_ANSWER:" in answer:
                        print(f"\n💡 Final Answer: {answer.split('FINAL_ANSWER:')[1].strip()}")
                        break
                    elif "FURTHER_PROCESSING_REQUIRED:" in answer:
                        user_input = answer.split("FURTHER_PROCESSING_REQUIRED:")[1].strip()
                        print(f"\n🔁 Further Processing Required: {user_input}")
                        continue  # 🧠 Re-run agent with updated input
                    else:
                        print(f"\n💡 Final Answer (raw): {answer}")
                        break
                else:
                    print(f"\n💡 Final Answer (unexpected): {result}")
                    break
    except KeyboardInterrupt:
        print("\n👋 Received exit signal. Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())



# Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.
# How much Anmol singh paid for his DLF apartment via Capbridge? 
# What do you know about Don Tapscott and Anthony Williams?
# What is the relationship between Gensol and Go-Auto?
# which course are we teaching on Canvas LMS? "How to use Canvas LMS.pdf"
# Summarize this page: https://theschoolof.ai/
# What is the log value of the amount that Anmol singh paid for his DLF apartment via Capbridge? 

# What is the name of the person who is the CEO of the company that is the parent company of Capbridge?
# Which is the parent company of Capbridge?  Who is the CEO of the parent company of Capbridge?
# What is the log value of the ascii value of the first character of the name of the person who is the CEO of the company that is the parent company of Capbridge?
# Which course do you recommend for learning from theschoolofai to learn about Agents? Recommend another course for Transformers & LLMs. https://theschoolof.ai/
# Which year did Agentic AI start?
# How many overs does a T20 match have?

# modifications:
# log mcp tool, input to plan (user ovverride), memory fix (todo), 
# modification of decision prompt to use history properly, modification of docstring to take 42.94 cr as 429400000 instead of 42 before taking log value
# 10 heuristics added to tools.py. Prioritize_search_tools adaed to the agent loop in loop.py
# Memory index properly (no tool = null) - merging of  
# merge type=='run_metadata' and corresponding type=='tool_output' done to create only one dictionary in memoryfor all steps (merge_memory_items() logic in memory.py) 
# Memory is updated properly with tool_output, input query and other metadata. This is used in loop.py inside run() using get_similar_memory_queries so that similar queries are not run again and again.   


# 
