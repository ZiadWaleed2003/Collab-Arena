"""
Base Memory Interface for CollabArena
Defines the abstract interface that all memory implementations must follow
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseMemory(ABC):
    """
    Abstract base class for memory implementations in CollabArena
    Defines the interface that all memory types must implement
    """
    
    def __init__(self):
        self.memory: Dict[str, Any] = {}
        self.access_log: List[Dict[str, Any]] = []
        self.agents: List[str] = []
    
    @abstractmethod
    def read(self, key: str, agent_id: str) -> Optional[Any]:
        """
        Read data from memory
        
        Args:
            key: Memory key to read
            agent_id: ID of the agent requesting access
            
        Returns:
            The stored value or None if not found/no access
        """
        pass
    
    @abstractmethod
    def write(self, key: str, value: Any, agent_id: str) -> bool:
        """
        Write data to memory
        
        Args:
            key: Memory key to write
            value: Value to store
            agent_id: ID of the agent requesting write access
            
        Returns:
            True if write successful, False otherwise
        """
        pass
    
    @abstractmethod
    def register_agent(self, agent_id: str) -> bool:
        """
        Register an agent for memory access
        
        Args:
            agent_id: ID of the agent to register
            
        Returns:
            True if registration successful
        """
        pass
    
    def on_agent_registered(self, agent_id: str) -> None:
        """
        Callback when an agent is registered
        Can be overridden by subclasses for specific behavior
        """
        pass
    
    def log_access(self, agent_id: str, operation: str, key: str, 
                   success: bool, timestamp: datetime = None) -> None:
        """
        Log memory access for audit trail
        
        Args:
            agent_id: ID of the agent accessing memory
            operation: Type of operation ('read' or 'write')
            key: Memory key being accessed
            success: Whether the operation was successful
            timestamp: When the access occurred (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        log_entry = {
            'agent_id': agent_id,
            'operation': operation,
            'key': key,
            'success': success,
            'timestamp': timestamp
        }
        self.access_log.append(log_entry)
    
    def get_access_log(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """
        Get access log, optionally filtered by agent
        
        Args:
            agent_id: If provided, filter log for this agent only
            
        Returns:
            List of log entries
        """
        if agent_id is None:
            return self.access_log.copy()
        
        return [entry for entry in self.access_log if entry['agent_id'] == agent_id]
    
    def clear_memory(self) -> None:
        """Clear all memory contents and logs"""
        self.memory.clear()
        self.access_log.clear()
    
    def get_memory_state(self) -> Dict[str, Any]:
        """
        Get current state of memory for debugging/monitoring
        
        Returns:
            Dictionary containing memory contents and metadata
        """
        return {
            'memory_contents': self.memory.copy(),
            'registered_agents': self.agents.copy(),
            'access_log_count': len(self.access_log),
            'memory_type': self.__class__.__name__
        }