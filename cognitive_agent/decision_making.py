from typing import Optional
from .models import Decision, ActionRequest, MemoryState, LLMResponse, ReasoningType

class DecisionMaker:
    def __init__(self, memory):
        self.memory = memory

    def make_decision(self, llm_response: LLMResponse) -> Optional[Decision]:
        """Make a decision based on LLM response and current memory state"""
        if llm_response.error:
            return Decision(
                action=ActionRequest(
                    tool_name="fallback_reasoning",
                    arguments={"error": llm_response.error}
                ),
                reasoning="Error occurred in LLM response",
                confidence=0.0
            )

        if llm_response.final_answer:
            return Decision(
                action=ActionRequest(
                    tool_name="final_answer",
                    arguments={"answer": llm_response.final_answer}
                ),
                reasoning="Final answer received",
                confidence=1.0
            )

        if llm_response.function_call:
            function_name = llm_response.function_call.name
            args = llm_response.function_call.args

            print('function_name = ' + str(function_name))
            # Validate the tool exists
            tool = self.memory.get_tool_by_name(function_name)
            if not tool:
                return Decision(
                    action=ActionRequest(
                        tool_name="fallback_reasoning",
                        arguments={"error": f"Unknown tool: {function_name}"}
                    ),
                    reasoning="Invalid tool requested",
                    confidence=0.0
                )

            # Validate arguments against tool schema
            if not self._validate_arguments(args, tool.input_schema):
                return Decision(
                    action=ActionRequest(
                        tool_name="fallback_reasoning",
                        arguments={"error": f"Invalid arguments for tool: {function_name}"}
                    ),
                    reasoning="Invalid arguments provided",
                    confidence=0.0
                )

            # Determine reasoning type based on tool
            reasoning_type = self._determine_reasoning_type(function_name)

            print("\n=== function_name ===" + str(function_name))
            print("\n=== args ===" + str(args))
            print("\n=== args type ===" + str(type(args)))
            print("\n=== reasoning_type ===" + str(reasoning_type))

            # Wrap steps in a dictionary for show_reasoning
            if function_name == "show_reasoning" or function_name == "check_consistency":
                args = {"steps": args}

            if function_name == "draw_rectangle":
                keys = ["x1", "y1", "x2", "y2"]
                args = dict(zip(keys, args))

            # if function_name == "add_text_in_paint":
            #     value = str(next(iter(args)))  # Get the first (and only) item from the set
            #     args = {"text": value}

            print("\n=== ActionRequest ===")
            return Decision(
                action=ActionRequest(
                    tool_name=function_name,
                    arguments=args
                ),
                reasoning=f"Executing {function_name} with validated arguments",
                confidence=0.9
            )
        
        return None

    def _validate_arguments(self, args: dict, schema: dict) -> bool:
        """Validate arguments against tool schema"""
        if not schema.get('properties'):
            return True

        for param_name, param_info in schema['properties'].items():
            if param_name not in args:
                if not param_info.get('required', False):
                    continue
                return False

            param_type = param_info.get('type')
            if param_type == 'integer':
                try:
                    int(args[param_name])
                except (ValueError, TypeError):
                    return False
            elif param_type == 'number':
                try:
                    float(args[param_name])
                except (ValueError, TypeError):
                    return False

        return True

    ARITHMETIC = "ARITHMETIC"
    LOGIC = "LOGIC"
    LOOKUP = "LOOKUP"
    GEOMETRY = "GEOMETRY"
    COMMON_SENSE = "COMMON_SENSE"
    PATTERN_RECOGNITION = "PATTERN_RECOGNITION"
    OTHER = "OTHER"

    def _determine_reasoning_type(self, tool_name: str) -> ReasoningType:
        """Determine the reasoning type based on tool name"""
        if tool_name in ["calculate", "verify"]:
            return ReasoningType.ARITHMETIC
        elif tool_name in ["show_reasoning", "check_consistency"]:
            return ReasoningType.LOGIC
        elif tool_name in ["open_paint", "draw_rectangle", "add_text_in_paint"]:
            return ReasoningType.GEOMETRY
        else:
            return ReasoningType.OTHER 