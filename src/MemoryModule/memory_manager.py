"""
Memory Manager for CollabArena
Provides unified interface for shared memory operations, short-term memory, and RBAC memory
"""

from typing import Any, Dict, List, Optional, Union
from .shared_memory import SharedMemory
from .short_term_memory import ShortTermMemory
from .rbac_memory import RBACMemory, AccessLevel

class MemoryManager:
    """
    Enhanced Memory Manager that handles shared memory, short-term memory, and RBAC memory.
    Supports composition with different memory implementations based on security requirements.
    """
    
    def __init__(self, memory_type: str = "shared", short_term_max_size: int = 50):
        """
        Initialize with specified memory implementation and short-term memory
        
        Args:
            memory_type: Type of memory implementation ("shared" or "rbac")
            short_term_max_size: Maximum size for short-term memory per agent
        """
        # Initialize primary memory implementation based on type
        if memory_type.lower() == "rbac":
            self.memory_impl = RBACMemory()
            self.memory_type = "rbac"
        else:
            self.memory_impl = SharedMemory()
            self.memory_type = "shared"
        
        # Short-term memory composition (same for all types)
        self.short_term_memories: Dict[str, ShortTermMemory] = {}
        self.short_term_max_size = short_term_max_size
    
    def register_agent(self, agent_id: str, role: str = None) -> bool:
        """
        Register an agent with the memory system
        
        Args:
            agent_id: Agent identifier
            role: Agent role (used for RBAC memory, ignored for shared memory)
        """
        # Register with primary memory implementation
        if self.memory_type == "rbac":
            success = self.memory_impl.register_agent(agent_id, role or "Guest")
        else:
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
    
    # RBAC-specific methods (only work when memory_type is "rbac")
    def set_agent_role(self, agent_id: str, new_role: str, admin_agent_id: str) -> bool:
        """
        Change an agent's role (RBAC only, requires admin privileges)
        """
        if self.memory_type != "rbac":
            return False
        
        return self.memory_impl.set_agent_role(agent_id, new_role, admin_agent_id)
    
    def add_role_permission(self, role: str, permission: str, admin_agent_id: str) -> bool:
        """
        Add permission to a role (RBAC only, requires admin privileges)
        
        Args:
            role: Role name
            permission: Permission name ("read", "write", "delete", "admin")
            admin_agent_id: Agent performing the action (must have admin access)
        """
        if self.memory_type != "rbac":
            return False
        
        try:
            access_level = AccessLevel(permission)
            return self.memory_impl.add_role_permission(role, access_level, admin_agent_id)
        except ValueError:
            return False
    
    def remove_role_permission(self, role: str, permission: str, admin_agent_id: str) -> bool:
        """
        Remove permission from a role (RBAC only, requires admin privileges)
        """
        if self.memory_type != "rbac":
            return False
        
        try:
            access_level = AccessLevel(permission)
            return self.memory_impl.remove_role_permission(role, access_level, admin_agent_id)
        except ValueError:
            return False
    
    def protect_key(self, key: str, admin_agent_id: str) -> bool:
        """
        Mark a memory key as protected (RBAC only, requires admin access)
        """
        if self.memory_type != "rbac":
            return False
        
        return self.memory_impl.protect_key(key, admin_agent_id)
    
    def unprotect_key(self, key: str, admin_agent_id: str) -> bool:
        """
        Remove protection from a memory key (RBAC only, requires admin access)
        """
        if self.memory_type != "rbac":
            return False
        
        return self.memory_impl.unprotect_key(key, admin_agent_id)
    
    def get_agent_permissions(self, agent_id: str) -> List[str]:
        """
        Get permissions for a specific agent (RBAC only)
        """
        if self.memory_type != "rbac":
            return []
        
        permissions = self.memory_impl.get_agent_permissions(agent_id)
        return [perm.value for perm in permissions]
    
    def get_role_info(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific role (RBAC only)
        """
        if self.memory_type != "rbac":
            return None
        
        return self.memory_impl.get_role_info(role)
    
    def get_all_roles(self) -> List[str]:
        """
        Get all available roles (RBAC only)
        """
        if self.memory_type != "rbac":
            return []
        
        return self.memory_impl.get_all_roles()
    
    def get_protected_keys(self, agent_id: str) -> List[str]:
        """
        Get list of protected keys (RBAC only, requires admin access)
        """
        if self.memory_type != "rbac":
            return []
        
        return self.memory_impl.get_protected_keys(agent_id)
    
    def get_rbac_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get RBAC system statistics (RBAC only)
        """
        if self.memory_type != "rbac":
            return None
        
        return self.memory_impl.get_rbac_stats()
    
    def is_rbac_enabled(self) -> bool:
        """
        Check if RBAC memory is enabled
        """
        return self.memory_type == "rbac"