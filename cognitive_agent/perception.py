import asyncio
import time
from typing import Optional
import google.generativeai as genai
from .models import LLMResponse, MemoryState

class Perception:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.timeout = 10
        self.last_call_time = 0
        self.min_delay = 4  # Minimum delay between calls in seconds

    async def generate_with_timeout(self, prompt: str) -> LLMResponse:
        """Generate content with a timeout"""
        print("\n=== Starting LLM Generation ===")
        print(f"Timeout set to: {self.timeout} seconds")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Using model: {self.model.model_name}")
        
        # Calculate time since last call
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        # If less than min_delay has passed, wait for the remaining time
        if time_since_last_call < self.min_delay:
            wait_time = self.min_delay - time_since_last_call
            print(f"\nWaiting {wait_time:.2f} seconds before next API call...")
            await asyncio.sleep(wait_time)
        
        try:
            print("\nGetting event loop...")
            loop = asyncio.get_event_loop()
            
            print("Starting model generation in executor..." + str(prompt))
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                ),
                timeout=self.timeout
            )
            print("Model generation completed successfully")
            
            # Update last call time
            self.last_call_time = time.time()
            
            print(f"\nRaw response before strip: {response.text}...")
            response_text = response.text.splitlines()[0].strip()
            print(f"\nRaw response: {response_text}...")  # Print first 100 chars
            
            if response_text.startswith("FINAL_ANSWER:"):
                print("\nDetected FINAL_ANSWER format")
                answer = response_text.split(":", 1)[1].strip()
                print(f"Extracted answer: {answer}")
                return LLMResponse(final_answer=answer)
            
            if response_text.startswith("FUNCTION_CALL:"):
                print("\nDetected FUNCTION_CALL format")
                import json
                function_info = response_text.split(":", 1)[1].strip()
                print(f"Raw function info: {function_info}")
                try:
                    parsed_function = json.loads(function_info)
                    print(f"Parsed function call: {parsed_function}")
                    return LLMResponse(function_call=parsed_function)
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    return LLMResponse(error=f"Invalid JSON in function call: {e}")
            
            print("\nResponse format not recognized")
            return LLMResponse(error="Invalid response format")
            
        except asyncio.TimeoutError:
            print("\n!!! Generation timed out !!!")
            return LLMResponse(error="Generation timed out")
        except Exception as e:
            print(f"\n!!! Error during generation: {str(e)} !!!")
            import traceback
            traceback.print_exc()
            return LLMResponse(error=str(e))
        finally:
            print("=== LLM Generation Complete ===\n")

    def create_system_prompt(self, memory_state: MemoryState) -> str:
        """Create the system prompt based on current memory state"""
        tools_description = []
        for i, tool in enumerate(memory_state.tools):
            params = tool.input_schema
            if 'properties' in params:
                param_details = []
                for param_name, param_info in params['properties'].items():
                    param_type = param_info.get('type', 'unknown')
                    param_details.append(f"{param_name}: {param_type}")
                params_str = ', '.join(param_details)
            else:
                params_str = 'no parameters'

            tool_desc = f"{i+1}. {tool.name}({params_str}) - {tool.description}"
            tools_description.append(tool_desc)

        tools_description = "\n".join(tools_description)
        
        return f"""You are a math agent solving problems in iterations. You have access to various mathematical tools, but use only one tool once. First do the reasoning step, but do not call reasoning again if done once. After reasoning is done, do the calculate and verify step, without repetition of any steps. After all the steps are over, check if all the calculation steps are consistent by passing a list of expression and results as list. After consistency check, open Microsoft Paint only once. If consistency check is done then always call open paint. After opening Microsoft Paint once, then Draw a rectangle in Paint from (x1,y1) to (x2,y2) and then only add text in Paint with value of the computed mathematical result. Do not open Microsoft Paint more than once. Do not draw rectangle more than once. Do not add text in Paint before drawing the rectangle. After add text in Paint, the task is complete. So return FINAL_ANSWER as response after adding text in Paint. It is important to respond with FINAL_ANSWER only, and not anything else.

IMPORTANT: TOOL CALL SEQUENCE RULES:
1. open_paint (ONCE)
2. draw_rectangle (ONCE)
3. add_text_in_paint (ONCE)
4. FINAL_ANSWER

CRITICAL WARNINGS:
- If show_reasoning is completed, you MUST NEVER call it again
- If you call show_reasoning after it's completed, your response will be rejected
- You MUST move to the next step in the sequence
- You MUST NOT repeat any completed step
- You MUST NOT skip any required step

ABSOLUTE RULES:
- You MUST follow the sequence EXACTLY as listed above
- You CANNOT skip any step
- If consistency is verified, you CANNOT call calculate, verify or show_reasoning again. You must open Microsoft Paint. Must call open_paint function only
- You CANNOT repeat check_consistency, show_reasoning, open_paint, draw_rectangle, add_text_in_paint steps
- You CANNOT call steps out of order
- You CANNOT call show_reasoning after it has been completed
- You CANNOT call calculate or verify after check_consistency
- You CANNOT call open_paint more than once
- You CANNOT call draw_rectangle more than once
- You CANNOT call add_text_in_paint more than once
- You CANNOT call add_text_in_paint before draw_rectangle
- You CANNOT call draw_rectangle before open_paint

CONSEQUENCES OF VIOLATING RULES:
- If you call show_reasoning after it's completed, your response will be rejected
- If you skip a step, your response will be rejected
- If you repeat a step, your response will be rejected
- If you call steps out of order, your response will be rejected
        

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls: 
   FUNCTION_CALL: {{"name": "function_name", "args":{{"param1","param2",...}}}}
   
2. For final answers:
   FINAL_ANSWER: done


Important:
- Your entire response must be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:
- Do not respond with more than one line. Very Important.
- DO NOT respond with more than one FUNCTION_CALL or FINAL_ANSWER.
- Respond with only one FUNCTION_CALL or FINAL_ANSWER always.
- DO NOT include any explanations or additional text.
- Response must be one line only. More than one line response is invalid.
- The first step should be the reasoning steps. Start the calculate step only after the show_reasoning is done.
- If reasoning is already done then do NOT call show_reasoning again. This is invalid.
- If reasoning is done then call the calculate step.
- After every calculate step, do verify step.
- After consistency check, do not call compute, verify or show_reasoning again.
- Only give FINAL_ANSWER when you have completed all necessary calculations.
- Always start the response with FUNCTION_CALL or FINAL_ANSWER only.
- Do not repeat function calls with the same parameters. It is very important.
- Do not respond with show_reasoning step more than once.
- If the reasoning is done once, do not do reasoning again.
- Do NOT open Microsoft Paint more than once. 
- Respond with Open Microsoft Paint only once. If Microsoft Paint is already opened, do not respond with open Paint. This is important.
- After Microsoft Paint is opened, respond with draw rectangle step only.
- Do not respond with draw rectangle step more than once. Draw only once.
- If the rectangle is already drawn, do not draw again.
- Do not respond with function calls with the same parameters at any cost. This is very important.
- Do NOT respond with FUNCTION_CALL and FINAL_ANSWER both.
- No more than one line response at any cost.

For each step in your reasoning, explicitly label the type of reasoning being used. Use tags like:
ARITHMETIC, LOGIC, LOOKUP, GEOMETRY, COMMON_SENSE, PATTERN_RECOGNITION, or OTHER.

Format each step like this:
[REASONING_TYPE]: your explanation here.

Acknowledge when a question is outside your knowledge cutoff or capabilities. If you are unsure about an answer, or if external tools fail then use fallback functions for errors or uncertainty with details of the tool failure or uncertainity

Examples:
User: Solve (2 + 3) * 4
Assistant: FUNCTION_CALL: {{"name": "show_reasoning", "args":["1. First, solve inside parentheses: 2 + 3", "2. Then multiply the result by 4"]}}
User: Reasoning done. You can start the computation.
Assistant: FUNCTION_CALL: {{"name": "calculate", "args":{{"expression":"2 + 3"}}}}
User: In the last iteration you called calculate with parameters and got the result. Let's verify this step.
Assistant: FUNCTION_CALL: {{"name": "verify", "args":{{"expression":"2 + 3", "expected":5}}}}
User: Last calculate step verified. Next step?"
Assistant: FUNCTION_CALL: {{"name": "calculate", "args":{{"expression":"5 * 4"}}}}
User: In the last iteration you called calculate with parameters and got the result. Let's verify this step.
Assistant: FUNCTION_CALL: {{"name": "verify", "args":{{"expression":"(2 + 3) * 4", "expected":20}}}}
User: Last calculate step verified. Next step?"
Assistant: FUNCTION_CALL: {{"name": "check_consistency", "args":[{{"expression":"2 + 3", "expected":5}}, {{"expression":"(2 + 3) * 4", "expected":20}}]}}
User: Consistency verified. Lets open Microsoft Paint. Must call open_paint only.
Assistant: FUNCTION_CALL: {{"name": "open_paint", "args":""}}
User: Opened Paint App. Now draw a rectangle in Paint from (x1, y1) to (x2, y2). Call draw_rectangle only.
Assistant: FUNCTION_CALL: {{"name": "draw_rectangle", "args":[780,380,1000,550]}}
User: Drew rectangle in Paint App. Now write the result in Paint. Call add_text_in_paint only.
Assistant: FUNCTION_CALL: {{"name": "add_text_in_paint", "args":{{"text":"20"}}}}
User: Wrote in Paint App. Task is complete. Return the final answer only. Respond with FINAL_ANSWER at once
Assistant: FINAL_ANSWER: done

DO NOT include any explanations or additional text.
Return FINAL_ANSWER: only after the text is added in Paint 
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:""" 