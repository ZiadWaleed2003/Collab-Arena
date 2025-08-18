"""
Workspace Manager for handling file operations and command execution.
This class provides a centralized way to manage workspace operations for LangGraph tools.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkspaceManager:
    """
    Manages workspace operations including file I/O and command execution.
    
    This class provides safe file operations and command execution with proper
    error handling for use with LangGraph tools.
    """
    
    def __init__(self, base_path: str = "./workspace"):
        """
        Initialize the workspace manager.
        
        Args:
            base_path: Base directory for workspace operations
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"Workspace manager initialized with base path: {self.base_path}")
    
    def _validate_path(self, path: str) -> Path:
        """
        Validate and normalize a file path within the workspace.
        
        Args:
            path: File path to validate
            
        Returns:
            Normalized Path object
            
        Raises:
            ValueError: If path is outside workspace or invalid
        """
        try:
            target_path = (self.base_path / path).resolve()
            # Ensure path is within workspace
            target_path.relative_to(self.base_path)
            return target_path
        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid path: {path}. Error: {str(e)}")
    
    def write_file(self, path: str, content: str, mode: str = "w") -> Dict[str, Any]:
        """
        Write content to a file with proper error handling.
        
        Args:
            path: Relative path to the file within workspace
            content: Content to write
            mode: Write mode ('w', 'a', 'x')
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Validate mode
            if mode not in ['w', 'a', 'x']:
                return {
                    "success": False,
                    "file_path": path,
                    "bytes_written": 0,
                    "message": f"Invalid mode '{mode}'. Use 'w', 'a', or 'x'."
                }
            
            target_path = self._validate_path(path)
            
            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists for 'x' mode
            if mode == 'x' and target_path.exists():
                return {
                    "success": False,
                    "file_path": str(target_path.relative_to(self.base_path)),
                    "bytes_written": 0,
                    "message": "File already exists (exclusive mode 'x')"
                }
            
            # Write the file
            with open(target_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            bytes_written = len(content.encode('utf-8'))
            relative_path = str(target_path.relative_to(self.base_path))
            
            logger.info(f"Successfully wrote {bytes_written} bytes to {relative_path}")
            
            return {
                "success": True,
                "file_path": relative_path,
                "bytes_written": bytes_written,
                "message": f"Successfully wrote {bytes_written} bytes to {relative_path}"
            }
            
        except ValueError as e:
            return {
                "success": False,
                "file_path": path,
                "bytes_written": 0,
                "message": f"Path validation error: {str(e)}"
            }
        except PermissionError:
            return {
                "success": False,
                "file_path": path,
                "bytes_written": 0,
                "message": f"Permission denied: Cannot write to {path}"
            }
        except OSError as e:
            return {
                "success": False,
                "file_path": path,
                "bytes_written": 0,
                "message": f"OS error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "file_path": path,
                "bytes_written": 0,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """
        Read content from a file with proper error handling.
        
        Args:
            path: Relative path to the file within workspace
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            target_path = self._validate_path(path)
            
            if not target_path.exists():
                return {
                    "success": False,
                    "content": "",
                    "file_path": path,
                    "message": f"File does not exist: {path}"
                }
            
            if not target_path.is_file():
                return {
                    "success": False,
                    "content": "",
                    "file_path": path,
                    "message": f"Path is not a file: {path}"
                }
            
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            relative_path = str(target_path.relative_to(self.base_path))
            
            return {
                "success": True,
                "content": content,
                "file_path": relative_path,
                "message": f"Successfully read {len(content)} characters from {relative_path}"
            }
            
        except ValueError as e:
            return {
                "success": False,
                "content": "",
                "file_path": path,
                "message": f"Path validation error: {str(e)}"
            }
        except PermissionError:
            return {
                "success": False,
                "content": "",
                "file_path": path,
                "message": f"Permission denied: Cannot read {path}"
            }
        except UnicodeDecodeError:
            return {
                "success": False,
                "content": "",
                "file_path": path,
                "message": f"Cannot decode file as UTF-8: {path}"
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "file_path": path,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def execute_command(self, cmd: str, timeout: int = 30, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a command with proper error handling and timeout.
        
        Args:
            cmd: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory (relative to workspace)
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Set working directory
            if cwd:
                work_dir = self._validate_path(cwd)
                if not work_dir.is_dir():
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"Working directory does not exist: {cwd}",
                        "exit_code": -1,
                        "execution_time": 0.0,
                        "command": cmd
                    }
            else:
                work_dir = self.base_path
            
            # Record start time
            start_time = time.time()
            
            # Execute command
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir)
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            logger.info(f"Command executed in {execution_time:.2f}s: {cmd[:50]}...")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time": execution_time,
                "command": cmd
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time if 'start_time' in locals() else timeout
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "exit_code": -1,
                "execution_time": execution_time,
                "command": cmd
            }
        except ValueError as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Path validation error: {str(e)}",
                "exit_code": -1,
                "execution_time": 0.0,
                "command": cmd
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unexpected error: {str(e)}",
                "exit_code": -1,
                "execution_time": 0.0,
                "command": cmd
            }
    
    def list_files(self, path: str = ".") -> Dict[str, Any]:
        """
        List files and directories in a path.
        
        Args:
            path: Relative path within workspace
            
        Returns:
            Dictionary with file listing
        """
        try:
            target_path = self._validate_path(path)
            
            if not target_path.exists():
                return {
                    "success": False,
                    "files": [],
                    "directories": [],
                    "path": path,
                    "message": f"Path does not exist: {path}"
                }
            
            if not target_path.is_dir():
                return {
                    "success": False,
                    "files": [],
                    "directories": [],
                    "path": path,
                    "message": f"Path is not a directory: {path}"
                }
            
            files = []
            directories = []
            
            for item in target_path.iterdir():
                relative_item = str(item.relative_to(self.base_path))
                if item.is_file():
                    files.append(relative_item)
                elif item.is_dir():
                    directories.append(relative_item)
            
            return {
                "success": True,
                "files": sorted(files),
                "directories": sorted(directories),
                "path": str(target_path.relative_to(self.base_path)),
                "message": f"Found {len(files)} files and {len(directories)} directories"
            }
            
        except ValueError as e:
            return {
                "success": False,
                "files": [],
                "directories": [],
                "path": path,
                "message": f"Path validation error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "files": [],
                "directories": [],
                "path": path,
                "message": f"Unexpected error: {str(e)}"
            }
