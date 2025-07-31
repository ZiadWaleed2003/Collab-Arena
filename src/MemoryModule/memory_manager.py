"""
Memory Manager for CollabArena
Provides unified interface for shared memory operations and short-term memory
"""

from typing import Any, Dict, List, Optional
from .shared_memory import SharedMemory
from .short_term_memory import ShortTermMemory

class MemoryManager:
    """
    Enhanced Memory Manager that handles both shared memory and short-term memory.
    All agents have full read/write access to the shared memory space and individual short-term memory.
    """
    
    def __init__(self, short_term_max_size: int = 50):
        """
        Initialize with shared memory implementation and short-term memory
        
        Args:
            short_term_max_size: Maximum size for short-term memory per agent
        """
        self.memory_impl = SharedMemory()
        self.memory_type = "shared"
        self.short_term_memories: Dict[str, ShortTermMemory] = {}
        self.short_term_max_size = short_term_max_size
    
    def register_agent(self, agent_id: str) -> bool:
        """Register an agent with the memory system"""
        success = self.memory_impl.register_agent(agent_id)
        
        # Create short-term memory for the agent
        if agent_id not in self.short_term_memories:
            self.short_term_memories[agent_id] = ShortTermMemory(self.short_term_max_size)
        
        return success
    
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
    
    # Short-term memory methods
    def add_short_term_event(self, agent_id: str, event: Any) -> bool:
        """Add an event to agent's short-term memory"""
        if agent_id not in self.short_term_memories:
            return False
        
        self.short_term_memories[agent_id].add_event(event)
        return True
    
    def get_recent_events(self, agent_id: str, limit: int) -> List[Any]:
        """Get recent events from agent's short-term memory"""
        if agent_id not in self.short_term_memories:
            return []
        
        return self.short_term_memories[agent_id].get_recent(limit)
    
    def get_recent_events_with_metadata(self, agent_id: str, limit: int) -> List[dict]:
        """Get recent events with metadata from agent's short-term memory"""
        if agent_id not in self.short_term_memories:
            return []
        
        return self.short_term_memories[agent_id].get_recent_with_metadata(limit)
    
    def clear_short_term_memory(self, agent_id: str) -> bool:
        """Clear agent's short-term memory"""
        if agent_id not in self.short_term_memories:
            return False
        
        self.short_term_memories[agent_id].clear()
        return True
    
    def get_short_term_memory_info(self, agent_id: str) -> Optional[dict]:
        """Get short-term memory information for an agent"""
        if agent_id not in self.short_term_memories:
            return None
        
        return self.short_term_memories[agent_id].get_memory_info()
    
    def get_all_short_term_events(self, agent_id: str) -> List[Any]:
        """Get all events from agent's short-term memory"""
        if agent_id not in self.short_term_memories:
            return []
        
        return self.short_term_memories[agent_id].get_all_events()
    
    def get_short_term_memory_size(self, agent_id: str) -> int:
        """Get current size of agent's short-term memory"""
        if agent_id not in self.short_term_memories:
            return 0
        
        return self.short_term_memories[agent_id].size()
    
    def is_short_term_memory_full(self, agent_id: str) -> bool:
        """Check if agent's short-term memory is full"""
        if agent_id not in self.short_term_memories:
            return False
        
        return self.short_term_memories[agent_id].is_full()