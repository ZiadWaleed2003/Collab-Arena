from typing import List, Optional, Dict, Any

from .search_tool import SearchingTool
from .code_writer_tool import CodeWriterTool
from .code_runner_tool import CodeRunnerTool
from .file_manager_tool import FileManagerTool

# Create instances of the tool classes
search_tool_instance = SearchingTool()
code_writer_tool_instance = CodeWriterTool()
code_runner_tool_instance = CodeRunnerTool()
file_manager_tool_instance = FileManagerTool()

# Tool registry for easy access - using the execute methods
AGENT_TOOLS = [
    search_tool_instance.execute,
    code_writer_tool_instance.execute,
    code_runner_tool_instance.execute,
    file_manager_tool_instance.execute
]

# Tool metadata for introspection
TOOL_METADATA = {
    "search_tool": {
        "name": "execute",  
        "description": "Search for information using queries",
        "parameters": ["query", "max_results"],
        "category": "information",
        "class": "SearchingTool"
    },
    "code_writer_tool": {
        "name": "execute", 
        "description": "Write code or text to files",
        "parameters": ["file_path", "content", "mode"],
        "category": "file_operations",
        "class": "CodeWriterTool"
    },
    "code_runner_tool": {
        "name": "execute",  
        "description": "Execute code files in various languages",
        "parameters": ["file_path", "language", "timeout"],
        "category": "execution",
        "class": "CodeRunnerTool"
    },
    "file_manager_tool": {
        "name": "execute",  
        "description": "Perform file system operations",
        "parameters": ["operation", "path"],
        "category": "file_operations",
        "class": "FileManagerTool"
    }
}


def get_available_tools() -> List[str]:
    """Get list of available tool names."""
    return list(TOOL_METADATA.keys())


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific tool."""
    return TOOL_METADATA.get(tool_name)


def get_tool_instances() -> Dict[str, Any]:
    """Get dictionary of tool instances for direct access."""
    return {
        "search_tool": search_tool_instance,
        "code_writer_tool": code_writer_tool_instance,
        "code_runner_tool": code_runner_tool_instance,
        "file_manager_tool": file_manager_tool_instance
    }


def get_tool_classes() -> Dict[str, Any]:
    """Get dictionary of tool classes for instantiation."""
    return {
        "SearchingTool": SearchingTool,
        "CodeWriterTool": CodeWriterTool,
        "CodeRunnerTool": CodeRunnerTool,
        "FileManagerTool": FileManagerTool
    }