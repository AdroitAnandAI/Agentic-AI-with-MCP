from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Union, Optional
from enum import Enum

class ReasoningType(str, Enum):
    ARITHMETIC = "ARITHMETIC"
    LOGIC = "LOGIC"
    LOOKUP = "LOOKUP"
    GEOMETRY = "GEOMETRY"
    COMMON_SENSE = "COMMON_SENSE"
    PATTERN_RECOGNITION = "PATTERN_RECOGNITION"
    OTHER = "OTHER"

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    def __str__(self):
        return f"Tool(name={self.name}, description={self.description})"

class ReasoningStep(BaseModel):
    type: ReasoningType
    explanation: str
    result: Optional[Any] = None

class MemoryState(BaseModel):
    iteration: int = 0
    last_response: Optional[str] = None
    iteration_responses: List[str] = Field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list)
    tools: List[Tool] = Field(default_factory=list)

    def __init__(self, **data):
        super().__init__(**data)
        print("\n=== Creating MemoryState ===")
        print(f"Tools in new state: {[tool.name for tool in self.tools]}")
        print("=== MemoryState Created ===\n")

class FunctionCall(BaseModel):
    name: str
    args: Union[List[str], List[Dict[str, Any]], Dict[str, Any], str, List[int]]  # Can be either a list or a dictionary

    @validator('args', pre=True)
    def validate_args(cls, v):
        print(f"\n=== Validating FunctionCall args ===")
        print(f"Args type: {type(v)}")
        print(f"Args value: {v}")
        if v == '':
            return {}  # or [] depending on how you want to treat empty args
        return v


class LLMResponse(BaseModel):
    function_call: Optional[FunctionCall] = None
    final_answer: Optional[str] = None
    error: Optional[str] = None

class ActionRequest(BaseModel):
    tool_name: str
    arguments: Union[List[str], Dict[str, Any]]  # Can be either a list or a dictionary

    @validator('arguments')
    def validate_arguments(cls, v, values):
        print(f"\n=== Validating ActionRequest arguments ===")
        print(f"Tool name: {values.get('tool_name')}")
        print(f"Arguments type: {type(v)}")
        print(f"Arguments value: {v}")
        
        # If it's a dictionary and the tool is show_reasoning, ensure it has a 'steps' key
        if isinstance(v, dict) and values.get('tool_name') == "show_reasoning":
            if 'steps' not in v:
                raise ValueError("show_reasoning tool requires a 'steps' key in the arguments dictionary")
            if not isinstance(v['steps'], list):
                raise ValueError("show_reasoning tool requires 'steps' to be a list")
        return v

class ReasoningRequest(BaseModel):
    tool_name: str
    arguments: Union[List[str], List[List[str]], List[Dict[str, Any]]]  # Removed Dict[str, Any]

    @validator('arguments')
    def validate_arguments(cls, v, values):
        print(f"\n=== Validating ReasoningRequest arguments ===")
        print(f"Tool name: {values.get('tool_name')}")
        print(f"Arguments type: {type(v)}")
        print(f"Arguments value: {v}")
        return v

    def get_arguments(self) -> Union[List[str], List[List[str]], List[Dict[str, Any]]]:
        """Return arguments in the format expected by the MCP server"""
        return self.arguments

class ActionResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None

class Decision(BaseModel):
    action: ActionRequest
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0) 