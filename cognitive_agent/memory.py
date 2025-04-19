from typing import List, Optional, Dict, Any
from .models import MemoryState, Tool, ReasoningStep, ActionResponse

class Memory:
    def __init__(self):
        self.state = MemoryState()
        self.long_term_memory: Dict[str, Any] = {}
        self.short_term_memory: Dict[str, Any] = {}
        print("Memory initialized with state:", self.state)

    def store_long_term(self, key: str, value: Any):
        """Store a value in long-term memory"""
        self.long_term_memory[key] = value
        print(f"Stored in long-term memory: {key} = {value}")

    def store_short_term(self, key: str, value: Any):
        """Store a value in short-term memory"""
        self.short_term_memory[key] = value
        print(f"Stored in short-term memory: {key} = {value}")

    def get_long_term(self, key: str) -> Optional[Any]:
        """Retrieve a value from long-term memory"""
        return self.long_term_memory.get(key)

    def get_short_term(self, key: str) -> Optional[Any]:
        """Retrieve a value from short-term memory"""
        return self.short_term_memory.get(key)

    def update_tools(self, tools: List[Tool]):
        """Update the available tools in memory"""
        print("\n=== Updating Tools in Memory ===")
        print(f"Number of tools to add: {len(tools)}")
        print("Tools:", [tool.name for tool in tools])
        self.state.tools = tools
        print("Current tools in memory:", [tool.name for tool in self.state.tools])
        print("=== Tools Update Complete ===\n")

    def add_reasoning_step(self, step: ReasoningStep):
        """Add a new reasoning step to memory"""
        self.state.reasoning_steps.append(step)

    def update_iteration(self, response: str, action_response: Optional[ActionResponse] = None):
        """Update the current iteration state"""
        self.state.iteration += 1
        self.state.last_response = response
        self.state.iteration_responses.append(response)
        
        if action_response and action_response.success:
            # Update the last reasoning step with the result if available
            if self.state.reasoning_steps:
                self.state.reasoning_steps[-1].result = action_response.result

    def reset(self):
        """Reset the memory state"""
        print("\n=== Resetting Memory ===")
        print("Tools before reset:", [tool.name for tool in self.state.tools])
        self.state = MemoryState()
        print("Memory reset complete")
        print("Tools after reset:", [tool.name for tool in self.state.tools])
        print("=== Memory Reset Complete ===\n")

    def get_state(self) -> MemoryState:
        """Get the current memory state"""
        return self.state

    def get_last_reasoning_step(self) -> Optional[ReasoningStep]:
        """Get the last reasoning step"""
        return self.state.reasoning_steps[-1] if self.state.reasoning_steps else None

    def get_tool_by_name(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by its name"""
        print("\n=== Looking up Tool ===")
        print(f"Looking for tool: {tool_name}")
        print("Available tools:", [tool.name for tool in self.state.tools])
        tool = next((tool for tool in self.state.tools if tool.name == tool_name), None)
        print(f"Found tool: {tool.name if tool else None}")
        print("=== Tool Lookup Complete ===\n")
        return tool 