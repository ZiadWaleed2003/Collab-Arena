"""
Tool Manager for managing and orchestrating tool instances.
Provides factory pattern for tool creation and management.
"""

from typing import Dict, List, Optional, Any
import logging

from .base_tool import BaseTool
from .utils import get_tool_classes, TOOL_METADATA
from ..workspace_manager import WorkspaceManager

# Configure logging
logger = logging.getLogger(__name__)


class ToolManager:
    """
    Factory for managing tool instances and providing tool execution capabilities.
    
    This class centralizes tool instantiation, management, and provides lookup
    capabilities for the Environment class and Action Executor.
    """
    
    def __init__(self, workspace_manager: WorkspaceManager):
        """
        Initialize the tool manager with a workspace manager.
        
        Args:
            workspace_manager: WorkspaceManager instance for tool operations
        """
        self.workspace_manager = workspace_manager
        self.available_tools: Dict[str, BaseTool] = {}
        
        # Use existing utilities instead of duplicating code
        self._tool_classes = get_tool_classes()
        self._tool_metadata = TOOL_METADATA.copy()
        
        # Initialize with default tools
        self.load_tools(list(self._tool_metadata.keys()))
        
        logger.info(f"ToolManager initialized with {len(self.available_tools)} tools")
    
    def load_tools(self, tool_names: List[str]) -> Dict[str, bool]:
        """
        Load specified tools into the manager.
        
        Args:
            tool_names: List of tool names to load
            
        Returns:
            Dictionary mapping tool names to success status
        """
        results = {}
        
        for tool_name in tool_names:
            try:
                if tool_name in self.available_tools:
                    logger.info(f"Tool '{tool_name}' already loaded")
                    results[tool_name] = True
                    continue
                
                tool_instance = self._create_tool(tool_name)
                if tool_instance:
                    self.available_tools[tool_name] = tool_instance
                    results[tool_name] = True
                    logger.info(f"Successfully loaded tool: {tool_name}")
                else:
                    results[tool_name] = False
                    logger.error(f"Failed to create tool: {tool_name}")
                    
            except Exception as e:
                results[tool_name] = False
                logger.error(f"Error loading tool '{tool_name}': {str(e)}")
        
        return results
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool instance by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance if found, None otherwise
        """
        tool = self.available_tools.get(tool_name)
        if not tool:
            logger.warning(f"Tool '{tool_name}' not found or not loaded")
        return tool
    
    def execute_tool(self, tool_name: str, state: dict, params: dict) -> Dict[str, Any]:
        """
        Execute a tool with the given state and parameters.
        
        Args:
            tool_name: Name of the tool to execute
            state: Current state dictionary
            params: Parameters dictionary to pass to the tool
            
        Returns:
            Dictionary with execution results
        """
        try:
            tool = self.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "result": None,
                    "message": f"Tool '{tool_name}' not found or not loaded"
                }
            
            # Execute the tool with correct signature
            result = tool.execute(state, params)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result,
                "message": f"Tool '{tool_name}' executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {
                "success": False,
                "tool_name": tool_name,
                "result": None,
                "message": f"Error executing tool '{tool_name}': {str(e)}"
            }
    
    def get_available_tool_names(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names that can be loaded
        """
        return list(self._tool_metadata.keys())
    
    def get_loaded_tool_names(self) -> List[str]:
        """
        Get list of currently loaded tool names.
        
        Returns:
            List of tool names that are currently loaded
        """
        return list(self.available_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata information for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool metadata dictionary if found, None otherwise
        """
        return self._tool_metadata.get(tool_name)
    
    def get_all_tool_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all available tools.
        
        Returns:
            Dictionary mapping tool names to their metadata
        """
        return self._tool_metadata.copy()
    
    def unload_tool(self, tool_name: str) -> bool:
        """
        Unload a tool from the manager.
        
        Args:
            tool_name: Name of the tool to unload
            
        Returns:
            True if successfully unloaded, False otherwise
        """
        if tool_name in self.available_tools:
            del self.available_tools[tool_name]
            logger.info(f"Tool '{tool_name}' unloaded")
            return True
        else:
            logger.warning(f"Tool '{tool_name}' not loaded, cannot unload")
            return False
    
    def reload_tool(self, tool_name: str) -> bool:
        """
        Reload a tool (unload and load again).
        
        Args:
            tool_name: Name of the tool to reload
            
        Returns:
            True if successfully reloaded, False otherwise
        """
        try:
            # Unload if loaded
            if tool_name in self.available_tools:
                self.unload_tool(tool_name)
            
            # Load again
            result = self.load_tools([tool_name])
            return result.get(tool_name, False)
            
        except Exception as e:
            logger.error(f"Error reloading tool '{tool_name}': {str(e)}")
            return False
    
    def _create_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Create a tool instance by name.
        
        Args:
            tool_name: Name of the tool to create
            
        Returns:
            Tool instance if successful, None otherwise
        """
        try:
            # Get tool metadata to find the class name
            tool_metadata = self._tool_metadata.get(tool_name)
            if not tool_metadata:
                logger.error(f"No metadata found for tool '{tool_name}'")
                return None
            
            # Get the class name from metadata
            class_name = tool_metadata.get('class')
            if not class_name:
                logger.error(f"No class name found in metadata for tool '{tool_name}'")
                return None
            
            # Get the actual class from the tool classes
            tool_class = self._tool_classes.get(class_name)
            if not tool_class:
                logger.error(f"Unknown tool class '{class_name}' for tool '{tool_name}'")
                return None
            
            # Create tool instance
            tool_instance = tool_class()
            
            # Set workspace manager if the tool has a workspace attribute
            if hasattr(tool_instance, 'workspace_manager'):
                tool_instance.workspace_manager = self.workspace_manager
            
            return tool_instance
            
        except Exception as e:
            logger.error(f"Error creating tool '{tool_name}': {str(e)}")
            return None

