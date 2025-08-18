"""
Environment Module Tools

This package contains LangGraph-compatible tools for the Collab-Arena project.
These tools replace the previous abstract class-based system with proper
@tool decorated functions that integrate seamlessly with LangGraph agents.

Available Tools:
- search_tool: Search for information using queries
- code_writer_tool: Write code or text to files
- code_runner_tool: Execute code files in various languages  
- file_manager_tool: Perform file system operations

Usage:
    from src.EnviromentModule.tools import LANGGRAPH_TOOLS
    
    # Use with LangGraph agent
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    
    agent = create_react_agent(ChatOpenAI(), LANGGRAPH_TOOLS)
"""

# Import all LangGraph tools
from .tools import (
    search_tool,
    code_writer_tool,
    code_runner_tool,
    file_manager_tool,
    LANGGRAPH_TOOLS,
    TOOL_METADATA,
    get_available_tools,
    get_tool_info
)

# Import workspace manager
from ..workspace_manager import WorkspaceManager

# Import agent example for demonstration
from .agent_example import CollabArenaAgent, demo_collaborative_workflow, simple_tool_demo

# Export everything for easy access
__all__ = [
    # Individual tools
    'search_tool',
    'code_writer_tool', 
    'code_runner_tool',
    'file_manager_tool',
    
    # Tool collections and metadata
    'LANGGRAPH_TOOLS',
    'TOOL_METADATA',
    'get_available_tools',
    'get_tool_info',
    
    # Workspace management
    'WorkspaceManager',
    
    # Agent and demo functions
    'CollabArenaAgent',
    'demo_collaborative_workflow',
    'simple_tool_demo'
]

# Version information
__version__ = "1.0.0"
__author__ = "Collab-Arena Team"
__description__ = "LangGraph-compatible tools for collaborative AI systems"