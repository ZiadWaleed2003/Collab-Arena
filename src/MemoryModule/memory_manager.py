"""
Memory Manager for CollabArena
Provides unified interface for shared memory operations
"""

from typing import Any, Dict, List, Optional
from .shared_memory import SharedMemory

class MemoryManager:
    """
    Simplified Memory Manager that handles only shared memory.
    All agents have full read/write access to the shared memory space.
    """
    
    def __init__(self):
        """Initialize with shared memory implementation"""
        self.memory_impl = SharedMemory()
        self.memory_type = "shared"
    
    def register_agent(self, agent_id: str) -> bool:
        """Register an agent with the memory system"""
        return self.memory_impl.register_agent(agent_id)
    
    def write(self, key: str, value: Any, agent_id: str) -> bool:
        """Write data to shared memory"""
        return self.memory_impl.write(key, value, agent_id)
    
    def read(self, key: str, agent_id: str) -> Any:
        """Read data from shared memory"""
        return self.memory_impl.read(key, agent_id)
    
    def get_value(self, key: str, agent_id: str) -> Any:
        """Get raw value without metadata"""
        return self.memory_impl.get_value(key, agent_id)
    
    def delete_key(self, key: str, agent_id: str) -> bool:
        """Delete a key from memory"""
        return self.memory_impl.delete_key(key, agent_id)
    
    def get_memory_keys(self) -> List[str]:
        """Get all available memory keys"""
        return self.memory_impl.get_memory_keys()
    
    def get_memory_state(self) -> Dict[str, Any]:
        """Get current memory state"""
        return self.memory_impl.get_memory_state()
    
    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get access log for audit purposes"""
        return self.memory_impl.get_access_log()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        return self.memory_impl.get_memory_stats()
    
    def get_agent_activity(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get activity statistics for a specific agent"""
        return self.memory_impl.get_agent_activity(agent_id)
    
    def clear_memory(self) -> bool:
        """Clear all memory contents"""
        return self.memory_impl.clear_memory()
    
    def get_memory_type(self) -> str:
        """Get the type of memory implementation"""
        return self.memory_type
