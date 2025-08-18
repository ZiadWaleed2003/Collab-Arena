import os
from typing import Any, Dict
from langchain_core.tools import tool
from src.EnviromentModule.workspace_manager import WorkspaceManager
from .base_tool import BaseTool


class CodeWriterTool(BaseTool):

    def __init__(self):
        super().__init__()


    @tool
    def execute(file_path: str, content: str, mode: str = "w") -> Dict[str, Any]:
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
            
            workspace_manager = WorkspaceManager()
            
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
        
    