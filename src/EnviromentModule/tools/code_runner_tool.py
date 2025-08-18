from typing import Any, Dict
from langchain_core.tools import tool

from .base_tool import BaseTool
from src.EnviromentModule.workspace_manager import WorkspaceManager
class CodeRunnerTool(BaseTool):

    def __init__(self):
        super().__init__()


    @tool
    def execute(self,file_path: str, language: str, timeout: int = 30) -> Dict[str, Any]:   
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

            workspace_manager = WorkspaceManager()
            
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