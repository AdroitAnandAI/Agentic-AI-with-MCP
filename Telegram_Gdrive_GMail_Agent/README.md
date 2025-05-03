# Telegram-GDrive-GMail Integration Agent

This project demonstrates an intelligent agent that integrates Telegram messaging with Google Drive and Gmail services. The agent processes user requests through a series of tools and services, enabling complex workflows like data collection, storage, and communication.

[![Watch the Demo](https://img.youtube.com/vi/OTtYoVwlHr8/0.jpg)](https://www.youtube.com/watch?v=OTtYoVwlHr8)

## Project Overview

The project consists of three main components:

1. **Telegram Bot Server** (`mcp_server_agent.py`)
   - Handles incoming Telegram messages
   - Manages user conversations
   - Routes messages to the agent for processing
   - Returns responses back to users

2. **Google Drive Integration** (`mcp_server_4.py`)
   - Manages Google Sheets operations
   - Creates and modifies spreadsheets
   - Handles data appending to sheets
   - Generates shareable sheet URLs

3. **Gmail Integration** (`mcp_server_6.py`)
   - Handles email operations
   - Sends emails with sheet links
   - Manages SMTP communication

## Usage Guide

1. **Initial Setup**:
   ```bash
   # Install required dependencies
   pip install -r requirements.txt
   ```

2. **Video Processing**:
   ```bash
   python mcp_server_agent.py
   ```

## System Flow

The system follows this general flow:

1. **Message Reception**
   - User sends a message to the Telegram bot
   - The bot server receives and processes the message
   - Acknowledgment is sent to the user

2. **Agent Processing**
   - The message is passed to the agent for analysis
   - The agent breaks down the request into actionable steps
   - Tools are selected and executed based on the task requirements

3. **Tool Execution**
   - Web search tools gather required information
   - Google Drive tools create and populate spreadsheets
   - Gmail tools send the final results

4. **Response Delivery**
   - The agent crafts a final response
   - The response is sent back to the user via Telegram

## Example Workflow

Let's walk through an example request:
"Find the Current Point Standings of F1 Racers, then put that into a Google Excel Sheet, and then share the link to this sheet with me on Gmail"

1. **Initial Processing**
   - User sends the message via Telegram
   - Bot server receives and acknowledges the message
   - Agent begins processing the request

2. **Data Collection**
   - Agent uses web search tools to find F1 standings
   - Results are collected and formatted

3. **Google Drive Integration**
   - A new Google Sheet is created
   - F1 standings data is appended to the sheet
   - A shareable link is generated

4. **Email Communication**
   - Agent uses Gmail integration to send an email
   - Email contains the Google Sheet link
   - Email is sent to the specified address

5. **Final Response**
   - Agent crafts a completion message
   - Response is sent back to the user via Telegram

You can try similar queries like this. For instance,
"Get the current weather conditions in Tokyo, then put that into a Google Excel Sheet, and then share the link to this sheet with me on Gmail"

You will get the current weather in Tokyo generated as a Google Sheet file in Google Drive.

## Technical Implementation

### Telegram Bot Server
- Uses FastAPI for the web server
- Implements SSE (Server-Sent Events) for real-time communication
- Manages user sessions and message queues

### Google Drive Integration
- Uses Google Sheets API
- Handles authentication via OAuth2
- Manages spreadsheet creation and modification

### Gmail Integration
- Uses SMTP for email communication
- Implements secure authentication
- Handles email composition and sending

## Setup and Configuration

1. **Environment Variables**
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `GMAIL_OAUTH_KEY`: Gmail OAuth credentials
   - `GEMINI_API_KEY`: Gemini API Key

2. **Google API Setup**
   - Configure Google Cloud Console
   - Set up OAuth2 credentials
   - Enable necessary APIs (Sheets, Drive)

3. **Dependencies**
   - Python 3.7+
   - Required packages listed in requirements.txt

## Security Considerations

- OAuth2 authentication for Google services
- Secure token storage
- Environment variable management
- SMTP security with TLS

## Future Enhancements

- Add more tool integrations
- Implement conversation history
- Add error recovery mechanisms
- Enhance response formatting
- Add support for file attachments
