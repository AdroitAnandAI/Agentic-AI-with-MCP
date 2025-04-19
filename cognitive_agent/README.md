# Cognitive Agent Architecture

This project implements a cognitive agent system that processes mathematical expressions and visualizes results using a four-layer cognitive architecture. The system combines mathematical reasoning with visualization capabilities through Microsoft Paint integration.

## Architecture Overview

The system is built around four cognitive layers that work together to process and execute tasks:

### 1. Perception Layer (`perception.py`)
- Interfaces with the LLM (Language Learning Model) for reasoning
- Generates system prompts based on current state
- Handles input processing and understanding
- Manages timeouts and response generation
- Creates structured prompts for mathematical problem-solving

### 2. Memory Layer (`memory.py`)
- Maintains both short-term and long-term memory
- Short-term memory: Stores temporary state, reasoning steps, and tool information
- Long-term memory: Stores persistent information like coordinate values for visualization
- Tracks iteration state and reasoning history
- Manages available tools and their states
- Stores fixed coordinates for rectangle drawing (x1=780, y1=380, x2=1000, y2=550)

### 3. Decision Making Layer (`decision_making.py`)
- Analyzes LLM responses to determine next actions
- Classifies reasoning types (ARITHMETIC, LOGIC, LOOKUP, etc.)
- Makes decisions about which tools to use
- Determines when to terminate the reasoning process
- Ensures consistent step-by-step problem solving

### 4. Action Layer (`action.py`)
- Executes decisions made by the decision-making layer
- Interfaces with external tools and services
- Handles tool execution and response processing
- Manages the MCP (Model Control Protocol) session
- Coordinates with Microsoft Paint for visualization

## Orchestrator (`main.py`)
The main orchestrator that:
- Initializes and coordinates all cognitive layers
- Manages the MCP client session
- Processes queries through the cognitive pipeline
- Handles tool registration and execution
- Maintains the conversation flow and state
- Stores and retrieves coordinates from long-term memory for visualization

## Data Models (`models.py`)
The system uses Pydantic models to define:
- `MemoryState`: Tracks the current state of the agent
- `Tool`: Defines available tools and their capabilities
- `ReasoningStep`: Records each step in the reasoning process
- `ActionResponse`: Handles responses from tool executions
- `ReasoningType`: Classifies different types of reasoning steps

## Usage

To run the cognitive agent from parent folder:

```bash
python -m cognitive_agent.main
```

The agent will:
1. Process mathematical expressions step by step
2. Verify each calculation
3. Visualize the results in Microsoft Paint
4. Draw a rectangle at fixed coordinates (stored in long-term memory)
5. Display the final result inside the rectangle

## Long-term Memory Usage

The system uses long-term memory to store fixed coordinates for visualization:
- x1 = 780, y1 = 380 (top-left corner)
- x2 = 1000, y2 = 550 (bottom-right corner)

These coordinates are stored during initialization and used consistently throughout the visualization process, ensuring the rectangle is always drawn at the same location.

## Environment Setup

The system requires:
- Python 3.7+
- MCP (Model Control Protocol) setup
- Microsoft Paint (for visualization)
- Environment variables:
  - `GEMINI_API_KEY`: API key for the LLM service

## Dependencies

- `mcp`: For model control protocol
- `pydantic`: For data validation and settings management
- `python-dotenv`: For environment variable management 