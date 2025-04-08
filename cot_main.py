import os
import re
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
import asyncio
from rich.console import Console
from rich.panel import Panel

console = Console()

# Load environment variables and setup Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    try:
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
        return response
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

async def get_llm_response(client, prompt):
    """Get response from LLM with timeout"""
    response = await generate_with_timeout(client, prompt)
    if response and response.text:
        return response.text.strip()
    return None

async def main():
    try:
        console.print(Panel("Chain of Thought Calculator", border_style="cyan"))

        server_params = StdioServerParameters(
            command="python",
            args=["cot_tools.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                system_prompt = """You are a mathematical reasoning agent that solves problems step by step.
You have access to these tools:
- show_reasoning(steps: list) - Show your step-by-step reasoning process
- calculate(expression: str) - Calculate the result of an expression
- verify(expression: str, expected: float) - Verify if a calculation is correct
- check_consistency(steps: list) - Check if calculation steps are consistent with each other
- fallback_reasoning(stepdesc: str) - Fallbacks for Errors or Uncertainty

First show your reasoning, then calculate and verify each step. After all steps are over, check if calculation steps are consistent by passing a list of expression and results as list. After consistency check, only return the FINAL_ANSWER finally and stop.

Respond with EXACTLY ONE line in one of these formats (no additional text):
1. FUNCTION_CALL: {"name": "function_name", "args":{"param1","param2",...}}
2. FINAL_ANSWER: [answer]

Important:
- Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:
- DO NOT include any explanations or additional text
- Response must be one line only. More than one line response is invalid
- Only give FINAL_ANSWER when you have completed all necessary calculations
- Always start the response with FUNCTION_CALL or FINAL_ANSWER only
- Do not repeat function calls with the same parameters
- Do not respond with function calls with the same parameters at any cost. This is important
- Do NOT respond with FUNCTION_CALL and FINAL_ANSWER both
- No more than one line response at any cost

For each step in your reasoning, explicitly label the type of reasoning being used. Use tags like:
ARITHMETIC, LOGIC, LOOKUP, GEOMETRY, COMMON_SENSE, PATTERN_RECOGNITION, or OTHER.

Format each step like this:
[REASONING_TYPE]: your explanation here.

Acknowledge when a question is outside your knowledge cutoff or capabilities. If you are unsure about an answer, or if external tools fail then use fallback functions for errors or uncertainty with details of the tool failure or uncertainity

Examples:
User: Solve (2 + 3) * 4
Assistant: FUNCTION_CALL: {"name": "show_reasoning", "args":["1. First, solve inside parentheses: 2 + 3", "2. Then multiply the result by 4"]}
User: Next step?
Assistant: FUNCTION_CALL: {"name": "calculate", "args":{"expression":"2 + 3"}}
User: Result is 5. Let's verify this step.
Assistant: FUNCTION_CALL: {"name": "verify", "args":{"expression":"2 + 3", expected:5}}
User: Verified. Next step?
Assistant: FUNCTION_CALL: {"name": "calculate", "args":{"expression":"5 * 4"}}
User: Result is 20. Let's verify the final answer.
Assistant: FUNCTION_CALL: {"name": "verify", "args":{"expression":"(2 + 3) * 4", expected:20}}
User: Verified correct.
Assistant: FINAL_ANSWER: [20]"""

                # problem = "[(23 + 7) * (15 - 8)] / [(56 - 45) * (33 + 21)] * [66 + 33]]"
                problem = "[(23 + 7) * (15 - 8)] * [66 + 33]"
                # problem = "[(23 + 7) * 15]"
                console.print(Panel(f"Problem: {problem}", border_style="cyan"))

                # Initialize conversation
                prompt = f"{system_prompt}\n\nSolve this problem step by step: {problem}"
                conversation_history = []

                while True:
                    response = await generate_with_timeout(client, prompt)
                    if not response or not response.text:
                        break

                    result = response.text.strip()
                    console.print(f"[red]=-[/red]"*25)
                    # print("=-"*25)
                    # Find the first occurrence of FUNCTION_CALL: or FINAL_ANSWER
                    match = re.search(r'FUNCTION_CALL:|FINAL_ANSWER', result)
                    if match:
                        # Strip everything to the left (keep the match and the rest)
                        trimmed = result[match.start():]
                        # Get only the first line
                        result = trimmed.splitlines()[0]
                    print(result)
                    console.print(f"[blue]=-[/blue]"*25)
                    console.print(f"\n[yellow]Assistant:[/yellow] {result}")

                    if result.startswith("FUNCTION_CALL:"):
                        _, function_info = result.split(":", 1)
                        print("*"*50)
                        print(function_info)
                        # parts = [p.strip() for p in function_info.split("|")]
                        # func_name = parts[0]
                        print("*"*52)
                        function_data = json.loads(function_info)
                        # print("after func data")
                        # print(function_data["args"])
                        parts = function_data["args"]
                        func_name = function_data["name"]                  

                        if func_name == "show_reasoning":
                            # steps = eval(parts['steps'])
                            await session.call_tool("show_reasoning", arguments={"steps": parts})
                            prompt += f"\nUser: Next step?"
                            
                        elif func_name == "calculate":
                            expression = parts['expression']
                            calc_result = await session.call_tool("calculate", arguments={"expression": expression})
                            # print(calc_result)
                            if calc_result.content:
                                value = calc_result.content[0].text
                                prompt += f"\nUser: Result is {value}. Let's verify this step."
                                conversation_history.append((expression, float(value)))
                                
                        elif func_name == "verify":
                            expression, expected = parts['expression'], float(parts['expected'])
                            await session.call_tool("verify", arguments={
                                "expression": expression,
                                "expected": expected
                            })
                            prompt += f"\nUser: Verified. Next step?"
                        elif func_name == "check_consistency":
                            # steps = parts['steps']
                            await session.call_tool("check_consistency", arguments={
                                "steps": parts
                            })
                            prompt += f"\nUser: Consistency verified. Arrive at final answer"
                        elif func_name == "fallback_reasoning":
                            expression = parts['expression']
                            await session.call_tool("fallback_reasoning", arguments={
                                "stepdesc": expression
                            })
                            prompt += f"\nUser: Fallback called. Next step?"
# - check_consistency(steps: list) - Check if calculation steps are consistent with each other
# - fallback_reasoning(stepdesc: str) - Fallbacks for Errors or Uncertainty

                    elif result.startswith("FINAL_ANSWER:"):
                        # Verify the final answer against the original problem
                        if conversation_history:
                            # print("result = " + str(result))
                            # print("result split = " + str(float(result.split("[")[1].split("]")[0])))
                            final_answer = float(result.split("[")[1].split("]")[0])
                            # print("final_answer = " + str(final_answer))
                            await session.call_tool("verify", arguments={ 
                                "expression": problem,
                                "expected": final_answer
                            })
                        break
                    
                    prompt += f"\nAssistant: {result}"

                console.print("\n[green]Calculation completed![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main())
