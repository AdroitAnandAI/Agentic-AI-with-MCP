import time
import os
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
# import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# max_iterations = 12
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcpserver_cot.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a math agent solving problems in iterations. You have access to various mathematical tools. First show your reasoning, then calculate and verify each step with expression inside each paranthesis. After all steps are over, check if calculation steps are consistent by passing a list of expression and results as list. After consistency check, open Microsoft Paint only once. After opening Microsoft Paint once, then Draw a rectangle in Paint from (x1,y1) to (x2,y2) where x1,y1,x2,y2 =780,380,1000,550 and then only add text in Paint with value of the computed mathematical result. Do not open Microsoft Paint more than once. Do not draw rectangle more than once. Do not add text in Paint before drawing the rectangle. After add text in Paint, the task is complete. So return FINAL_ANSWER as response after adding text in Paint. It is important to respond with FINAL_ANSWER only, and not anything else.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls: 
   FUNCTION_CALL: {{"name": "function_name", "args":{{"param1","param2",...}}}}
   
2. For final answers:
   FINAL_ANSWER: Done


Important:
- Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:
- DO NOT include any explanations or additional text
- Response must be one line only. More than one line response is invalid
- If show_reasoning is done once then do NOT ever call show_reasoning again. This is invalid
- Only give FINAL_ANSWER when you have completed all necessary calculations
- Always start the response with FUNCTION_CALL or FINAL_ANSWER only
- Do not repeat function calls with the same parameters
- Do not respond with show_reasoning step more than once
- If the reasoning is done once, do not do reasoning again
- Do NOT open Microsoft Paint more than once. 
- Respond with Open Microsoft Paint only once. If Microsoft Paint is already opened, do not respond with open Paint. This is important
- Do not respond with draw rectangle step more than once. Draw only once
- If the rectangle is already drawn, do not draw again
- Do not respond with function calls with the same parameters at any cost. This is very important
- Do NOT respond with FUNCTION_CALL and FINAL_ANSWER both
- No more than one line response at any cost

For each step in your reasoning, explicitly label the type of reasoning being used. Use tags like:
ARITHMETIC, LOGIC, LOOKUP, GEOMETRY, COMMON_SENSE, PATTERN_RECOGNITION, or OTHER.

Format each step like this:
[REASONING_TYPE]: your explanation here.

Acknowledge when a question is outside your knowledge cutoff or capabilities. If you are unsure about an answer, or if external tools fail then use fallback functions for errors or uncertainty with details of the tool failure or uncertainity

Examples:
User: Solve (2 + 3) * 4
Assistant: FUNCTION_CALL: {{"name": "show_reasoning", "args":["1. First, solve inside parentheses: 2 + 3", "2. Then multiply the result by 4"]}}
User: Next step?
Assistant: FUNCTION_CALL: {{"name": "calculate", "args":{{"expression":"2 + 3"}}}}
User: Result is 5. Let's verify this step.
Assistant: FUNCTION_CALL: {{"name": "verify", "args":{{"expression":"2 + 3", "expected":5}}}}
User: Verified. Next step?
Assistant: FUNCTION_CALL: {{"name": "calculate", "args":{{"expression":"5 * 4"}}}}
User: Result is 20. Let's verify the final answer.
Assistant: FUNCTION_CALL: {{"name": "verify", "args":{{"expression":"(2 + 3) * 4", "expected":20}}}}
User: Verified correct.
Assistant: FUNCTION_CALL: {{"name": "open_paint", "args":""}}
User: Opened Paint App
Assistant: FUNCTION_CALL: {{"name": "draw_rectangle", "args":[780,380,1000,550]}}
User: Drew rectangle in Paint App
Assistant: FUNCTION_CALL: {{"name": "add_text_in_paint", "args":{{"20"}}}}
User: Wrote in Paint App
Assistant: FINAL_ANSWER: Done

DO NOT include any explanations or additional text.
Return FINAL_ANSWER: only after the text is added in Paint 
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                # query = """[(23 + 7) * 15]"""
                query = """[(24 + sqrt(36)) * (15 - 8)] * sin(30) / [(56 - 45) * (33 + 21)] * [66 + 33]]"""
                # query = """((60 + sqrt(36)) * sin(30)) / ((9 + cos(60)) * tan(45) + sqrt(49)) + log(1000)"""

                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                externalTool = False

                # Initialize conversation
                prompt = f"{system_prompt}\n\nSolve this problem step by step: {query}"

                while True: # iteration < max_iterations
                    # Gemini free version supports only 15 requests in a minute
                    # hence giving a sleep interval of 4s when external tool (Paint) is not active
                    if not externalTool:
                        time.sleep(3)

                    print(f"\n--- Iteration {iteration + 1} ---")

                    if not externalTool:
                        # print('prompt = ' + prompt[-100:])
                        current_query = prompt
                    else:
                        # if last_response is None:
                        #     current_query = query
                        # else:
                        print('iteration_response = ' + str(iteration_response))
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                        # Get model's response with timeout
                        print("Preparing to generate LLM response...")
                        prompt = f"{system_prompt}\n\nQuery: {current_query}"

                        # print('prompt = ' + prompt[-100:])
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        if response_text.startswith("FINAL_ANSWER:"):                                
                            break  
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        print("*"*50)
                        print(function_info)
                        # parts = [p.strip() for p in function_info.split("|")]
                        # func_name = parts[0]
                        print("*"*50)
                        function_data = json.loads(function_info)
                        # print("after func data")
                        # print(function_data["args"])
                        params = function_data["args"]
                        func_name = function_data["name"]  

                        # if func_name == "calculate":
                        #     params = params['expression']
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        # print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")


                            # _, function_info = result.split(":", 1)
                            # print("*"*50)
                            # print(function_info)
                            # # parts = [p.strip() for p in function_info.split("|")]
                            # # func_name = parts[0]
                            # print("*"*52)
                            # function_data = json.loads(function_info)
                            # # print("after func data")
                            # # print(function_data["args"])
                            # parts = function_data["args"]
                            # func_name = function_data["name"]                  

                            if func_name == "show_reasoning":
                                # steps = eval(parts['steps'])
                                await session.call_tool("show_reasoning", arguments={"steps": params})
                                prompt += f"\nUser: Reasoning done. You can start to calculate the result"
                                
                            elif func_name == "calculate":
                                expression = params['expression']
                                calc_result = await session.call_tool("calculate", arguments={"expression": expression})
                                # print(calc_result)
                                if calc_result.content:
                                    value = calc_result.content[0].text
                                    prompt += f"\n\nIn the {iteration + 1} iteration you called {func_name} with {expression} parameters, and the function returned {value}.\n User: Result is {value}. Let's verify this step."
                                    # conversation_history.append((expression, float(value)))
                                    
                            elif func_name == "verify":
                                expression, expected = params['expression'], float(params['expected'])
                                print("expression = " + str(expression))
                                print("expected = " + str(expected))
                                await session.call_tool("verify", arguments={
                                    "expression": expression,
                                    "expected": expected
                                })
                                prompt += f"\nUser: Verified. Next step?"
                            elif func_name == "check_consistency":
                                # steps = parts['steps']
                                await session.call_tool("check_consistency", arguments={
                                    "steps": params
                                })
                                prompt += f"\nUser: Consistency verified. Next step?"
                            elif func_name == "fallback_reasoning":
                                # steps = parts['steps']
                                await session.call_tool("fallback_reasoning", arguments={
                                    "stepdesc": params
                                })
                                prompt += f"\nUser: Fallback called. Next step?"
                            else:

                                # Prepare arguments according to the tool's input schema
                                arguments = {}
                                schema_properties = tool.inputSchema.get('properties', {})
                                print(f"DEBUG: Schema properties: {schema_properties}")

                                for param_name, param_info in schema_properties.items():
                                    if not params:  # Check if we have enough parameters
                                        raise ValueError(f"Not enough parameters provided for {func_name}")
                                        
                                    if isinstance(params, dict):
                                        # If value is a dictionary, get 'text' from params dictionary
                                        if 'x1' in params:
                                            value = list(params.values())
                                            param_info['type'] = 'array'
                                        else:
                                            value = params['text']
                                    else:
                                        value = params.pop(0)  # Get and remove the first parameter

                                    param_type = param_info.get('type', 'string')
                                    
                                    print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                    
                                    # Convert the value to the correct type based on the schema
                                    if param_type == 'integer':
                                        arguments[param_name] = int(value)
                                    elif param_type == 'number':
                                        arguments[param_name] = float(value)
                                    elif param_type == 'array':
                                        # Handle array input
                                        if isinstance(value, str):
                                            value = value.strip('[]').split(',')
                                        arguments[param_name] = [int(x) for x in value]
                                        # arguments[param_name] = params
                                    else:
                                        arguments[param_name] = str(value)

                                print(f"DEBUG: Final arguments: {arguments}")
                                print(f"DEBUG: Calling tool {func_name}")
                                
                                result = await session.call_tool(func_name, arguments=arguments)
                                print(f"DEBUG: Raw result: {result}")
                            
                                # Get the full result content
                                if hasattr(result, 'content'):
                                    print(f"DEBUG: Result has content attribute")
                                    # Handle multiple content items
                                    if isinstance(result.content, list):
                                        iteration_result = [
                                            item.text if hasattr(item, 'text') else str(item)
                                            for item in result.content
                                        ]
                                    else:
                                        iteration_result = str(result.content)
                                else:
                                    print(f"DEBUG: Result has no content attribute")
                                    iteration_result = str(result)
                                    
                                print(f"DEBUG: Final iteration result: {iteration_result}")
                                
                                # Format the response based on result type
                                if isinstance(iteration_result, list):
                                    result_str = json.loads(iteration_result[0])["content"][0]["text"]
                                else:
                                    result_str = str(iteration_result)

                                iteration_response.append(
                                    f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                    f"and the function returned {result_str}."
                                )
                                last_response = iteration_result

                            if response_text.startswith("FINAL_ANSWER:"):                                
                                break  

                            if func_name in {"show_reasoning", "calculate", "verify", "check_consistency"}:
                                externalTool = False
                            else:
                                externalTool = True

                            print('externalTool = ' + str(externalTool))
                            
                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    # elif response_text.startswith("FINAL_ANSWER:"):
                    #     print("\n=== Agent Execution Complete ===")
                    #     result = await session.call_tool("open_paint")
                    #     print(result.content[0].text)

                    #     # Wait longer for Paint to be fully maximized
                    #     await asyncio.sleep(1)

                    #     # Draw a rectangle
                    #     result = await session.call_tool(
                    #         "draw_rectangle",
                    #         arguments={
                    #             "x1": 780,
                    #             "y1": 380,
                    #             "x2": 1000,
                    #             "y2": 550
                    #         }
                    #     )
                    #     print(result.content[0].text)

                    #     # Draw rectangle and add text
                    #     result = await session.call_tool(
                    #         "add_text_in_paint",
                    #         arguments={
                    #             "text": response_text
                    #         }
                    #     )
                    #     print(result.content[0].text)
                    #     break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
