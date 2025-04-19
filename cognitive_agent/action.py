import asyncio
from typing import Dict, Any
from mcp import ClientSession
from .models import ActionRequest, ActionResponse, Tool
import anyio

class ActionExecutor:
    def __init__(self, session: ClientSession):
        self.session = session

    async def execute_action(self, action: ActionRequest) -> ActionResponse:
        """Execute an action using the MCP session"""
        try:
            print('**************action.tool_name = ' + str(action.tool_name))
            print('**************action.arguments = ' + str(action.arguments))
            
            # Check if session is still valid
            if not self.session or not hasattr(self.session, 'call_tool'):
                return ActionResponse(
                    success=False,
                    result=None,
                    error="MCP session is not properly initialized"
                )
            
            result = await self.session.call_tool(
                action.tool_name,
                arguments=action.arguments
            )

            print('**************result = ' + str(result))

            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    result_text = [
                        item.text if hasattr(item, 'text') else str(item)
                        for item in result.content
                    ]
                else:
                    result_text = str(result.content)
            else:
                result_text = str(result)

            return ActionResponse(
                success=True,
                result=result_text
            )

        except anyio.ClosedResourceError as e:
            import traceback
            error_msg = f"MCP server connection closed. Please check if the server is running. Error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return ActionResponse(
                success=False,
                result=None,
                error=error_msg
            )
        except Exception as e:
            import traceback
            error_msg = f"Error executing action {action.tool_name}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return ActionResponse(
                success=False,
                result=None,
                error=error_msg
            )

    async def execute_final_answer(self, answer: str) -> ActionResponse:
        """Execute the final answer action"""
        try:
            # Open Paint
            result = await self.session.call_tool("open_paint")
            if not hasattr(result, 'content') or not result.content:
                return ActionResponse(
                    success=False,
                    result=None,
                    error="Failed to open Paint"
                )

            # Wait for Paint to be fully maximized
            await asyncio.sleep(1)

            # Draw rectangle
            result = await self.session.call_tool(
                "draw_rectangle",
                arguments={
                    "x1": 780,
                    "y1": 380,
                    "x2": 1000,
                    "y2": 550
                }
            )

            # Add text
            result = await self.session.call_tool(
                "add_text_in_paint",
                arguments={
                    "text": answer
                }
            )

            return ActionResponse(
                success=True,
                result="Final answer displayed in Paint"
            )

        except Exception as e:
            return ActionResponse(
                success=False,
                result=None,
                error=str(e)
            ) 