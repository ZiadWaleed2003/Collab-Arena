"""
LangGraph Tools for Environment Module

This module contains LangGraph @tool decorated functions that replace the 
previous class-based tool system. All tools return structured dictionaries
and handle errors gracefully without raising exceptions to LangGraph.
"""

import asyncio
import json
import os
import subprocess
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests
from langchain_core.tools import tool

from ..workspace_manager import WorkspaceManager

# Initialize workspace manager
workspace_manager = WorkspaceManager()


@tool
def search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search for information using the provided query.
    
    This tool performs web search or knowledge base search to find relevant
    information based on the query. It handles rate limiting and provides
    structured results.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Dictionary containing:
        - results: List of search results with title, snippet, and url
        - total_found: Total number of results found
        - query_used: The actual query used for searching
        - success: Boolean indicating if search was successful
        - message: Status message or error description
    """
    try:
        # Validate inputs
        if not query or not isinstance(query, str):
            return {
                "results": [],
                "total_found": 0,
                "query_used": query,
                "success": False,
                "message": "Invalid query: must be a non-empty string"
            }
        
        if not isinstance(max_results, int) or max_results < 1:
            max_results = 5
        
        # Clean and prepare query
        cleaned_query = query.strip()[:500]  # Limit query length
        

        """
            actual implementation still in progress here for this tool
            maybe I'll use tavily and firecrawl or scrapegraph still didn't decided yet
        """
        
        # return {
        #     "results": mock_results,
        #     "total_found": len(mock_results),
        #     "query_used": cleaned_query,
        #     "success": True,
        #     "message": f"Found {len(mock_results)} results for query: {cleaned_query}"
        # }
        
    except Exception as e:
        return {
            "results": [],
            "total_found": 0,
            "query_used": query if isinstance(query, str) else "",
            "success": False,
            "message": f"Search error: {str(e)}"
        }


@tool
def code_writer_tool(file_path: str, content: str, mode: str = "w") -> Dict[str, Any]:
    """Write code or text content to a file in the workspace.
    
    This tool creates or modifies files in the workspace with proper error
    handling and validation. It supports different write modes and creates
    directories as needed.
    
    Args:
        file_path: Relative path to the file within workspace
        content: Content to write to the file
        mode: Write mode - 'w' (write/overwrite), 'a' (append), 'x' (exclusive create)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation succeeded
        - file_path: The actual file path used
        - bytes_written: Number of bytes written
        - message: Status message or error description
        - file_info: Additional file metadata (size, created, etc.)
    """
    try:
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            return {
                "success": False,
                "file_path": file_path,
                "bytes_written": 0,
                "message": "Invalid file_path: must be a non-empty string",
                "file_info": {}
            }
        
        if not isinstance(content, str):
            return {
                "success": False,
                "file_path": file_path,
                "bytes_written": 0,
                "message": "Invalid content: must be a string",
                "file_info": {}
            }
        
        if mode not in ['w', 'a', 'x']:
            return {
                "success": False,
                "file_path": file_path,
                "bytes_written": 0,
                "message": f"Invalid mode '{mode}': must be 'w', 'a', or 'x'",
                "file_info": {}
            }
        
        # Use workspace manager to write file
        result = workspace_manager.write_file(file_path, content, mode)
        
        # Add file info if successful
        if result["success"]:
            try:
                full_path = workspace_manager.base_path / result["file_path"]
                stat = full_path.stat()
                result["file_info"] = {
                    "size_bytes": stat.st_size,
                    "created_time": stat.st_ctime,
                    "modified_time": stat.st_mtime,
                    "is_readable": os.access(full_path, os.R_OK),
                    "is_writable": os.access(full_path, os.W_OK)
                }
            except Exception:
                result["file_info"] = {}
        else:
            result["file_info"] = {}
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path if isinstance(file_path, str) else "",
            "bytes_written": 0,
            "message": f"Unexpected error in code_writer_tool: {str(e)}",
            "file_info": {}
        }


@tool
def code_runner_tool(file_path: str, language: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute code files in various programming languages.
    
    This tool executes code files with proper timeout handling and security
    considerations. It captures both stdout and stderr and provides detailed
    execution information.
    
    Args:
        file_path: Relative path to the file to execute
        language: Programming language (python, javascript, bash, etc.)
        timeout: Maximum execution time in seconds (default: 30)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if execution completed without errors
        - stdout: Standard output from execution
        - stderr: Standard error output
        - exit_code: Process exit code
        - execution_time: Time taken to execute in seconds
        - language_used: The language interpreter used
        - message: Status message or error description
    """
    try:
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            return {
                "success": False,
                "stdout": "",
                "stderr": "Invalid file_path: must be a non-empty string",
                "exit_code": -1,
                "execution_time": 0.0,
                "language_used": language,
                "message": "Invalid file path"
            }
        
        if not language or not isinstance(language, str):
            return {
                "success": False,
                "stdout": "",
                "stderr": "Invalid language: must be a non-empty string",
                "exit_code": -1,
                "execution_time": 0.0,
                "language_used": language,
                "message": "Invalid language specification"
            }
        
        if not isinstance(timeout, int) or timeout < 1:
            timeout = 30
        
        # Check if file exists
        file_result = workspace_manager.read_file(file_path)
        if not file_result["success"]:
            return {
                "success": False,
                "stdout": "",
                "stderr": file_result["message"],
                "exit_code": -1,
                "execution_time": 0.0,
                "language_used": language,
                "message": f"Cannot read file: {file_result['message']}"
            }
        
        # Define language command mappings
        language_commands = {
            "python": ["python3", "-u"],
            "python3": ["python3", "-u"],
            "javascript": ["node"],
            "js": ["node"],
            "bash": ["bash"],
            "sh": ["sh"],
            "ruby": ["ruby"],
            "go": ["go", "run"],
            "java": ["java"],  # Requires compilation first
            "cpp": ["g++", "-o", "/tmp/output", "&&", "/tmp/output"],
            "c": ["gcc", "-o", "/tmp/output", "&&", "/tmp/output"]
        }
        
        lang_key = language.lower()
        if lang_key not in language_commands:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "exit_code": -1,
                "execution_time": 0.0,
                "language_used": language,
                "message": f"Language '{language}' is not supported. "
                          f"Supported: {', '.join(language_commands.keys())}"
            }
        
        # Build command
        cmd_parts = language_commands[lang_key]
        full_path = workspace_manager.base_path / file_path
        
        # Special handling for compiled languages
        if lang_key in ["java", "cpp", "c"]:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Compiled languages require additional setup",
                "exit_code": -1,
                "execution_time": 0.0,
                "language_used": language,
                "message": f"Compiled language '{language}' requires compilation step"
            }
        
        # Build final command
        if lang_key in ["bash", "sh"]:
            command = f"{' '.join(cmd_parts)} {full_path}"
        else:
            command = f"{' '.join(cmd_parts)} {full_path}"
        
        # Execute using workspace manager
        result = workspace_manager.execute_command(command, timeout)
        
        # Format result for code runner
        return {
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "execution_time": result["execution_time"],
            "language_used": language,
            "message": f"Executed {language} code in {result['execution_time']:.2f}s"
        }
        
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unexpected error: {str(e)}",
            "exit_code": -1,
            "execution_time": 0.0,
            "language_used": language if isinstance(language, str) else "",
            "message": f"Unexpected error in code_runner_tool: {str(e)}"
        }


@tool  
def file_manager_tool(operation: str, path: str, **kwargs) -> Dict[str, Any]:
    """Perform file management operations in the workspace.
    
    This tool provides file system operations like listing directories,
    reading files, checking file existence, and getting file metadata.
    
    Args:
        operation: Operation to perform ('list', 'read', 'exists', 'info')
        path: File or directory path (relative to workspace)
        **kwargs: Additional arguments for specific operations
        
    Returns:
        Dictionary with operation results and metadata
    """
    try:
        if not operation or not isinstance(operation, str):
            return {
                "success": False,
                "operation": operation,
                "path": path,
                "result": None,
                "message": "Invalid operation: must be a non-empty string"
            }
        
        if not path or not isinstance(path, str):
            return {
                "success": False,
                "operation": operation,
                "path": path,
                "result": None,
                "message": "Invalid path: must be a non-empty string"
            }
        
        operation = operation.lower()
        
        if operation == "list":
            result = workspace_manager.list_files(path)
            return {
                "success": result["success"],
                "operation": "list",
                "path": result["path"],
                "result": {
                    "files": result["files"],
                    "directories": result["directories"]
                },
                "message": result["message"]
            }
        
        elif operation == "read":
            result = workspace_manager.read_file(path)
            return {
                "success": result["success"],
                "operation": "read",
                "path": result["file_path"],
                "result": {
                    "content": result["content"]
                },
                "message": result["message"]
            }
        
        elif operation == "exists":
            try:
                full_path = workspace_manager.base_path / path
                exists = full_path.exists()
                is_file = full_path.is_file() if exists else False
                is_dir = full_path.is_dir() if exists else False
                
                return {
                    "success": True,
                    "operation": "exists",
                    "path": path,
                    "result": {
                        "exists": exists,
                        "is_file": is_file,
                        "is_directory": is_dir
                    },
                    "message": f"Path {'exists' if exists else 'does not exist'}: {path}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "operation": "exists",
                    "path": path,
                    "result": None,
                    "message": f"Error checking path existence: {str(e)}"
                }
        
        elif operation == "info":
            try:
                full_path = workspace_manager.base_path / path
                if not full_path.exists():
                    return {
                        "success": False,
                        "operation": "info",
                        "path": path,
                        "result": None,
                        "message": f"Path does not exist: {path}"
                    }
                
                stat = full_path.stat()
                info = {
                    "size_bytes": stat.st_size,
                    "created_time": stat.st_ctime,
                    "modified_time": stat.st_mtime,
                    "accessed_time": stat.st_atime,
                    "is_file": full_path.is_file(),
                    "is_directory": full_path.is_dir(),
                    "permissions": oct(stat.st_mode)[-3:],
                    "owner_readable": os.access(full_path, os.R_OK),
                    "owner_writable": os.access(full_path, os.W_OK),
                    "owner_executable": os.access(full_path, os.X_OK)
                }
                
                return {
                    "success": True,
                    "operation": "info",
                    "path": path,
                    "result": info,
                    "message": f"Retrieved info for: {path}"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "operation": "info",
                    "path": path,
                    "result": None,
                    "message": f"Error getting file info: {str(e)}"
                }
        
        else:
            return {
                "success": False,
                "operation": operation,
                "path": path,
                "result": None,
                "message": f"Unsupported operation: {operation}. "
                          "Supported: list, read, exists, info"
            }
    
    except Exception as e:
        return {
            "success": False,
            "operation": operation if isinstance(operation, str) else "",
            "path": path if isinstance(path, str) else "",
            "result": None,
            "message": f"Unexpected error in file_manager_tool: {str(e)}"
        }


# Tool registry for easy access
LANGGRAPH_TOOLS = [
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
        "parameters": ["query", "max_results"],
        "category": "information"
    },
    "code_writer_tool": {
        "name": "code_writer_tool", 
        "description": "Write code or text to files",
        "parameters": ["file_path", "content", "mode"],
        "category": "file_operations"
    },
    "code_runner_tool": {
        "name": "code_runner_tool",
        "description": "Execute code files in various languages",
        "parameters": ["file_path", "language", "timeout"],
        "category": "execution"
    },
    "file_manager_tool": {
        "name": "file_manager_tool",
        "description": "Perform file system operations",
        "parameters": ["operation", "path"],
        "category": "file_operations"
    }
}


def get_available_tools() -> List[str]:
    """Get list of available tool names."""
    return list(TOOL_METADATA.keys())


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific tool."""
    return TOOL_METADATA.get(tool_name)
