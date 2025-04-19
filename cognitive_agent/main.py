import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .perception import Perception
from .memory import Memory
from .decision_making import DecisionMaker
from .action import ActionExecutor
from .models import Tool, ReasoningStep, ReasoningType

class CognitiveAgent:
    def __init__(self, api_key: str):
        self.memory = Memory()
        self.perception = Perception(api_key)
        self.decision_maker = DecisionMaker(self.memory)
        self.action_executor = None  # Will be initialized with session
        self.iteration_response = []  # Track iteration responses
        self.externalTool = False  # Track if external tool is active

        # Store coordinates in long-term memory
        self.memory.store_long_term("x1", 780)
        self.memory.store_long_term("y1", 380)
        self.memory.store_long_term("x2", 1000)
        self.memory.store_long_term("y2", 550)

    async def process_query(self, query: str):
        """Process a query through the cognitive layers"""
        # Reset memory state and iteration tracking
        self.iteration_response = []
        self.externalTool = False

        # Create system prompt
        system_prompt = self.perception.create_system_prompt(self.memory.get_state())
        prompt = f"{system_prompt}\n\nSolve this problem step by step: {query}"

        # Get the absolute path to mcpserver_cot.py
        current_dir = Path(__file__).parent
        server_script = current_dir / "mcpserver_cot.py"
        
        if not server_script.exists():
            raise FileNotFoundError(f"MCP server script not found at {server_script}")

        print('server_script = ' + str(server_script))
        
        # Create server parameters
        print("Creating server parameters...")
        try:
            server_params = StdioServerParameters(
                command="python",
                args=[str(server_script)]
            )

            # Connect to the MCP server and process query
            print("Connecting to MCP server...")
            async with stdio_client(server_params) as (read, write):
                print("Created stdio client, initializing session...")
                async with ClientSession(read, write) as session:
                    print("Session created, initializing...")
                    try:
                        await session.initialize()
                        print("Session initialized successfully")
                    except Exception as e:
                        print(f"Error during session initialization: {str(e)}")
                        raise
                    
                    self.action_executor = ActionExecutor(session)
                    print("Action executor created")
                    
                    # Get available tools
                    print("Requesting tools from session...")
                    try:
                        tools_result = await session.list_tools()
                        print(f"Tools result received: {tools_result}")
                        print(f"Number of tools in result: {len(tools_result.tools) if hasattr(tools_result, 'tools') else 'tools attribute not found'}")
                        
                        if not hasattr(tools_result, 'tools') or not tools_result.tools:
                            print("Warning: No tools found in tools_result")
                            return
                            
                        tools = [
                            Tool(
                                name=tool.name,
                                description=getattr(tool, 'description', 'No description available'),
                                input_schema=tool.inputSchema,
                                output_schema={}  # Empty schema since it's not available
                            )
                            for tool in tools_result.tools
                        ]
                        print(f"Converted {len(tools)} tools to Tool objects")
                        self.memory.update_tools(tools)
                        print(f"Updated memory with {len(tools)} tools")
                    except Exception as e:
                        print(f"Error during tool registration: {str(e)}")
                        raise

                    # Process the query
                    while True:
                        # Add delay when external tool is not active
                        if not self.externalTool:
                            time.sleep(3)  # 3 second delay between iterations

                        print(f"\n--- Iteration {self.memory.get_state().iteration + 1} ---")            

                        # Perception: Get LLM response
                        llm_response = await self.perception.generate_with_timeout(prompt)
                        
                        # Decision Making: Determine next action
                        decision = self.decision_maker.make_decision(llm_response)
                        if not decision:
                            break

                        print('decision.action.tool_name = ' + str(decision.action.tool_name))

                        # Action: Execute the decision
                        if decision.action.tool_name == "final_answer":
                            action_response = await self.action_executor.execute_final_answer(
                                decision.action.arguments["answer"]
                            )
                        else:
                            action_response = await self.action_executor.execute_action(decision.action)

                        # Memory: Update state
                        self.memory.update_iteration(
                            response=str(decision.action),
                            action_response=action_response
                        )

                        print('action_response  = ' + str(action_response.success))
                        print('action_response err = ' + str(action_response.error))
                        if action_response.success:
                            # Add reasoning step to memory
                            self.memory.add_reasoning_step(
                                ReasoningStep(
                                    type=self.decision_maker._determine_reasoning_type(decision.action.tool_name),
                                    explanation=decision.reasoning,
                                    result=action_response.result
                                )
                            )

                            # Update iteration response
                            if isinstance(action_response.result, list):
                                result_str = action_response.result[0]
                            else:
                                result_str = str(action_response.result)

                            self.iteration_response.append(
                                f"In the {self.memory.get_state().iteration} iteration you called {decision.action.tool_name} with {decision.action.arguments} parameters, "
                                f"and the function returned {result_str}."
                            )

                            print('decision.action.tool_name = ' + str(decision.action.tool_name))
                            if decision.action.tool_name == "show_reasoning":
                                prompt += f"\nUser: Reasoning is already done. You can call calculate step now."
                            if decision.action.tool_name == "calculate":
                                prompt += f"\n\nIn the {self.memory.get_state().iteration} iteration you called {decision.action.tool_name} with {decision.action.arguments} parameters and got the result {result_str}. Let's verify this step."
                            if decision.action.tool_name == "verify":
                                prompt += f"\nUser: Last calculate step verified. Next step?"
                            if decision.action.tool_name == "check_consistency":
                                prompt += f"\nUser: Consistency verified. Lets open Microsoft Paint. Must call open_paint only"
                            if decision.action.tool_name == "open_paint":
                                x1 = self.memory.get_long_term("x1")
                                y1 = self.memory.get_long_term("y1")
                                x2 = self.memory.get_long_term("x2")
                                y2 = self.memory.get_long_term("y2")
                                prompt += f"\nUser: Opened Paint App. Now draw a rectangle in Paint from ({x1}, {y1}) to ({x2}, {y2}). Call draw_rectangle with {x1}, {y1}) to ({x2}, {y2} only, NOT add_text_in_paint. Return FUNCTION_CALL only."
                            if decision.action.tool_name == "draw_rectangle":
                                prompt += f"\nUser: User: Drawn a rectangle in Paint App. Now call the add_text_in_paint function only, to write the result in Paint inside the rectangle. Do NOT respond with FINAL_ANSWER."
                            if decision.action.tool_name == "add_text_in_paint":
                                prompt += f"\nUser: Wrote in Paint App. Task is complete. Return the final answer only. Respond with FINAL_ANSWER at once."
                            if decision.action.tool_name == "fallback_reasoning":
                                prompt += f"\nUser: Fallback called. Next step?"

                        # Update externalTool flag based on the tool used
                        if decision.action.tool_name in {"show_reasoning", "calculate", "verify", "check_consistency"}:
                            self.externalTool = False
                        else:
                            self.externalTool = True

                        print('Tool name = ' + str(decision.action.tool_name))
                        print('externalTool = ' + str(self.externalTool))

                        if llm_response.final_answer:
                            break

        except Exception as e:
            print(f"Error during MCP client setup or query processing: {str(e)}")
            raise

    async def initialize(self):
        """Initialize the agent with MCP session"""
        # This method is now a no-op since initialization is handled in process_query
        pass

async def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

    # Create and initialize agent
    agent = CognitiveAgent(api_key)
    await agent.initialize()

    # Process query
    # query = "[(24 + sqrt(36)) * (15 - 8)] * sin(30) / [(56 - 45) * (33 + 21)] * [66 + 33]"
    # query = "[(23 + 7) * 15]"
    # query = "[(24 + 36) * (15 - 8)] * 30 / [(56 - 45) * (33 + 21)] * [66 + 33]"
    query = "[(24 + 36) * (15 - 8)] * 30 / [(56 - 45) * (33 + 21)]"
    await agent.process_query(query)

if __name__ == "__main__":
    asyncio.run(main()) 