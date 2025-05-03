from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp import types
import sys
import os
import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import yaml
from core.loop import AgentLoop
from core.session import MultiMCP

# Initialize FastMCP server with SSE transport
mcp = FastMCP("telegram-bot")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store for active conversations
active_conversations: Dict[int, asyncio.Queue] = {}

# Create FastAPI app
app = FastAPI()

async def process_with_agent(message: str) -> str:
    """Process a message through the agent and return the final answer."""
    try:
        # Load MCP server configs from profiles.yaml
        with open("config/profiles.yaml", "r") as f:
            profile = yaml.safe_load(f)
            mcp_servers = profile.get("mcp_servers", [])

        multi_mcp = MultiMCP(server_configs=mcp_servers)
        await multi_mcp.initialize()

        agent = AgentLoop(
            user_input=message,
            dispatcher=multi_mcp
        )

        final_response = await agent.run()
        return final_response.replace("FINAL_ANSWER:", "").strip()

    except Exception as e:
        logger.error(f"Agent processing failed: {e}")
        return f"Error processing message: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and pass them to the agent."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    logger.info(f"Received message from user {user_id}: {message_text}")
    
    # Send acknowledgment
    await update.message.reply_text("Message received, processing...")
    
    # Process message through agent
    try:
        final_answer = await process_with_agent(message_text)
        await update.message.reply_text(final_answer)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(f"Error processing message: {str(e)}")

async def send_response(update: Update, response: str) -> None:
    """Send the agent's response back to the user."""
    await update.message.reply_text(response)

@mcp.tool()
async def get_next_message(user_id: int) -> str:
    """
    Get the next message from a specific user's queue.
    
    Args:
        user_id: The Telegram user ID to get messages from
    """
    logger.info(f"Waiting for message from user {user_id}")
    if user_id not in active_conversations:
        active_conversations[user_id] = asyncio.Queue()
    
    try:
        # Wait for a message with a timeout
        message = await asyncio.wait_for(active_conversations[user_id].get(), timeout=300)
        logger.info(f"Got message from user {user_id}: {message}")
        return message
    except asyncio.TimeoutError:
        logger.info(f"Timeout waiting for message from user {user_id}")
        return ""

@mcp.tool()
async def send_telegram_message(user_id: int, message: str) -> str:
    """
    Send a message to a specific Telegram user.
    
    Args:
        user_id: The Telegram user ID to send the message to
        message: The message to send
    """
    try:
        # Get the application instance
        app = Application.get_current()
        if app is None:
            return "Error: Telegram application not initialized"
        
        # Send the message
        await app.bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Sent message to user {user_id}: {message}")
        return f"Message sent to user {user_id}"
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return f"Error sending message: {str(e)}"

async def start_bot(token: str):
    """Start the Telegram bot."""
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    await application.initialize()
    await application.start()
    logger.info("Telegram bot started")
    
    # Start polling in the background
    await application.updater.start_polling()

async def startup_event():
    """Initialize the Telegram bot when the FastAPI app starts."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("Error: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    await start_bot(token)

# Add startup event handler
app.add_event_handler("startup", startup_event)

# Add MCP SSE endpoints to FastAPI app
@app.get("/mcp/events")
async def mcp_events(request: Request):
    """SSE endpoint for MCP events."""
    async def event_generator():
        try:
            async for event in mcp.event_stream():
                yield {
                    "event": event.type,
                    "data": event.data
                }
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            yield {
                "event": "error",
                "data": str(e)
            }

    return EventSourceResponse(event_generator())

@app.post("/mcp/call")
async def mcp_call(request: Request):
    """Handle MCP tool calls."""
    data = await request.json()
    tool_name = data.get("tool")
    arguments = data.get("arguments", {})
    
    if not hasattr(mcp, tool_name):
        return JSONResponse({"error": f"Tool {tool_name} not found"}, status_code=404)
    
    tool = getattr(mcp, tool_name)
    result = await tool(**arguments)
    return JSONResponse({"result": result})

@app.get("/mcp/tools")
async def mcp_tools():
    """List available MCP tools."""
    tools = []
    for name in dir(mcp):
        if name.startswith("_") or not callable(getattr(mcp, name)):
            continue
        tools.append({"name": name})
    return JSONResponse({"tools": tools})

if __name__ == "__main__":
    print("MCP Server Agent starting with SSE transport")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
