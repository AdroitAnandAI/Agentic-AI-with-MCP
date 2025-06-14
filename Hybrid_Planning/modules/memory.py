# modules/memory.py

import json
import os
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Optional fallback logger
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

def merge_memory_items(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge run_metadata and tool_output items.
    Takes 'text' from run_metadata and adds it as 'input_query' to corresponding tool_output.
    """
    merged = []
    metadata_text = None
    
    for item in raw:
        if item.get('type') == 'run_metadata':
            # Extract query from metadata text
            text = item.get('text', '')
            if 'input:' in text.lower():
                metadata_text = text.split('input:', 1)[1].strip()
            continue
            
        if item.get('type') == 'tool_output' and metadata_text:
            # Add input_query to tool_output
            item['input_query'] = metadata_text
            metadata_text = None  # Reset for next pair
            
        merged.append(item)
    
    return merged

class MemoryItem(BaseModel):
    """Represents a single memory entry for a session."""
    timestamp: float
    type: str  # run_metadata, tool_call, tool_output, final_answer
    text: str
    input_query: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[dict] = None
    final_answer: Optional[str] = None
    tags: Optional[List[str]] = []
    success: Optional[bool] = None
    metadata: Optional[dict] = {}  # ✅ ADD THIS LINE BACK


class MemoryManager:
    """Manages session memory (read/write/append)."""

    def __init__(self, session_id: str, memory_dir: str = "memory"):
        self.session_id = session_id
        self.memory_dir = memory_dir
        self.memory_path = os.path.join('memory', session_id.split('-')[0], session_id.split('-')[1], session_id.split('-')[2], f'session-{session_id}.json')
        self.items: List[MemoryItem] = []

        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

        self.load()

    def load(self):
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self.items = [MemoryItem(**item) for item in raw]
        else:
            self.items = []

    def save(self):
        # Before opening the file for writing
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as f:
            raw = [item.dict() for item in self.items]
            if raw:  # Only save if we have items
                merged = merge_memory_items(raw)
                json.dump(merged, f, indent=2)

    def add(self, item: MemoryItem):
        self.items.append(item)
        self.save()

    def add_tool_call(
        self, tool_name: str, tool_args: dict, tags: Optional[List[str]] = None
    ):
        item = MemoryItem(
            timestamp=time.time(),
            type="tool_call",
            text=f"Called {tool_name} with {tool_args}",
            tool_name=tool_name,
            tool_args=tool_args,
            tags=tags or [],
        )
        self.add(item)

    def add_tool_output(
        self, tool_name: str, tool_args: dict, tool_result: dict, success: bool, tags: Optional[List[str]] = None
    ):
        item = MemoryItem(
            timestamp=time.time(),
            type="tool_output",
            text=f"Output of {tool_name}: {tool_result}",
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            success=success,  # 🆕 Track success!
            tags=tags or [],
        )
        self.add(item)

    def add_final_answer(self, text: str):
        item = MemoryItem(
            timestamp=time.time(),
            type="final_answer",
            text=text,
            final_answer=text,
        )
        self.add(item)

    def find_recent_successes(self, limit: int = 5) -> List[str]:
        """Find tool names which succeeded recently."""
        tool_successes = []

        # Search from newest to oldest
        for item in reversed(self.items):
            if item.type == "tool_output" and item.success:
                if item.tool_name and item.tool_name not in tool_successes:
                    tool_successes.append(item.tool_name)
            if len(tool_successes) >= limit:
                break

        return tool_successes

    def add_tool_success(self, tool_name: str, success: bool):
        """Patch last tool call or output for a given tool with success=True/False."""

        # Search backwards for latest matching tool call/output
        for item in reversed(self.items):
            if item.tool_name == tool_name and item.type in {"tool_call", "tool_output"}:
                item.success = success
                log("memory", f"✅ Marked {tool_name} as success={success}")
                self.save()
                return

        log("memory", f"⚠️ Tried to mark {tool_name} as success={success} but no matching memory found.")

    def get_session_items(self) -> List[MemoryItem]:
        """
        Return all memory items for current session.
        """
        return self.items
