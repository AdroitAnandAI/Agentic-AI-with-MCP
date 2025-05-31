# Hybrid Planning Agent

This project implements an intelligent agent system that combines hybrid planning with memory-indexing and safe Python code execution inside a sandbox. The system is designed to handle complex tasks through a combination of planning, execution, and memory management.

## Key Components

### 1. Hybrid Planning
The system implements a hybrid planning approach in `loop.py` that combines:
- Conservative planning mode for single-step tool execution
- Exploratory planning mode for multi-step tool execution
- Memory-based fallback mechanisms for improved reliability
- Maximum step and lifeline limits for controlled execution

### 2. Heuristics and Planning Strategies
The planning system in `loop.py` implements several heuristics:
- Tool prioritization based on query characteristics
- Memory-based fallback for failed tool executions
- Similar query detection for reusing successful solutions
- Step-by-step execution with lifeline management
- Support for both synchronous and asynchronous tool execution

### 3. Python Sandbox Execution
The system includes a secure Python code execution environment:
- Isolated execution environment for running agent-generated code
- Limited access to built-in functions and modules
- Controlled tool call interface with rate limiting
- Error handling and result formatting
- Support for both synchronous and asynchronous code execution

### 4. Memory Management
The system implements sophisticated memory management:
- Session-based memory storage
- Memory indexing for quick retrieval
- Similar query detection using word overlap similarity
- Memory-based fallback for failed tool executions
- Historical conversation tracking and retrieval

### 5. Tool Integration
The system integrates with multiple tool servers:
- Math tools for numerical computations
- Document processing tools for text analysis
- Web search tools for information retrieval
- Memory tools for conversation history management

## Usage

To run the agent:

1. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

2. Run the agent:
```bash
python agent.py
```

The agent will:
1. Accept user input
2. Process the input through the hybrid planning system
3. Execute appropriate tools in a sandboxed environment
4. Store results in memory for future reference
5. Return the final answer or request further processing

## Configuration

The system can be configured through:
- `config/profiles.yaml` for tool server configuration
- Strategy profiles for planning behavior
- Memory settings for storage and retrieval
- Sandbox settings for code execution

## Architecture

The system follows a modular architecture:
- `core/` - Core system components
- `modules/` - Functional modules
- `config/` - Configuration files
- `memory/` - Memory storage
- `prompts/` - Planning prompts

## Security

The system implements several security measures:
- Sandboxed Python code execution
- Limited tool access
- Rate limiting for tool calls
- Memory isolation between sessions
- Input validation and sanitization 