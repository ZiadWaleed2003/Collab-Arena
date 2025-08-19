import os
from typing import Any, Dict
from langchain_core.tools import tool

from src.EnviromentModule.workspace_manager import WorkspaceManager



@tool  
def file_manager_tool(tool_input:dict) -> Dict[str, Any]:
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
            path = tool_input.get('path','')
            operation = tool_input.get('operation','')
    

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
            workspace_manager = WorkspaceManager()
            
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