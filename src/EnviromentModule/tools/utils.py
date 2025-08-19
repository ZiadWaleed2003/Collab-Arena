from typing import List, Optional, Dict, Any, Callable

from .search_tool import search_tool
from .code_writer_tool import code_writer_tool
from .code_runner_tool import code_runner_tool
from .file_manager_tool import file_manager_tool

# Tool registry for easy access - using the langraph decorated functions
AGENT_TOOLS = [
    search_tool,
    code_writer_tool,
    code_runner_tool,
    file_manager_tool
]

# Tool metadata for introspection
TOOL_METADATA = {
    "search_tool": {
        "name": "search_tool",  
        "description": "Search for information using queries",
        "parameters": ["query"],
        "category": "information",
        "function": search_tool
    },
    "code_writer_tool": {
        "name": "code_writer_tool", 
        "description": "Write code or text to files",
        "parameters": ["file_path", "content", "mode"],
        "category": "file_operations",
        "function": code_writer_tool
    },
    "code_runner_tool": {
        "name": "code_runner_tool",  
        "description": "Execute code files in various languages",
        "parameters": ["file_path", "language", "timeout"],
        "category": "execution",
        "function": code_runner_tool
    },
    "file_manager_tool": {
        "name": "file_manager_tool",  
        "description": "Perform file system operations",
        "parameters": ["operation", "path"],
        "category": "file_operations",
        "function": file_manager_tool
    }
}


def get_available_tools() -> List[str]:
    """Get list of available tool names."""
    return list(TOOL_METADATA.keys())


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific tool."""
    return TOOL_METADATA.get(tool_name)


def get_tool_functions() -> Dict[str, Callable]:
    """Get dictionary of tool functions for direct access."""
    return {
        "search_tool": search_tool,
        "code_writer_tool": code_writer_tool,
        "code_runner_tool": code_runner_tool,
        "file_manager_tool": file_manager_tool
    }


def get_tool_function(tool_name: str) -> Optional[Callable]:
    """Get a specific tool function by name."""
    tool_functions = get_tool_functions()
    return tool_functions.get(tool_name)