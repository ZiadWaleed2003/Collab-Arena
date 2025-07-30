"""
Shared Memory Implementation for CollabArena
All registered agents can read and write to shared memory space
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_memory import BaseMemory


class SharedMemory(BaseMemory):
    """
    Shared memory implementation where all registered agents can read and write
    All agents have equal access to all memory locations
    """
    
    def __init__(self):
        super().__init__()
        self.memory: Dict[str, Any] = {}
    
    def read(self, key: str, agent_id: str) -> Optional[Any]:
        """
        Read data from shared memory
        All registered agents can read any key
        """
        # Check if agent is registered
        if agent_id not in self.agents:
            self.log_access(agent_id, 'read', key, success=False)
            return None
        
        # Try to read the value
        if key in self.memory:
            value = self.memory[key]
            self.log_access(agent_id, 'read', key, success=True)
            return value
        else:
            self.log_access(agent_id, 'read', key, success=False)
            return None
    
    def write(self, key: str, value: Any, agent_id: str) -> bool:
        """
        Write data to shared memory
        All registered agents can write to any key
        """
        # Check if agent is registered
        if agent_id not in self.agents:
            self.log_access(agent_id, 'write', key, success=False)
            return False
        
        # Write the value with metadata
        self.memory[key] = {
            'value': value,
            'written_by': agent_id,
            'timestamp': datetime.now(),
            'version': self._get_next_version(key)
        }
        
        self.log_access(agent_id, 'write', key, success=True)
        return True
    
    def register_agent(self, agent_id: str) -> bool:
        """
        Register an agent for shared memory access
        """
        if agent_id not in self.agents:
            self.agents.append(agent_id)
            self.on_agent_registered(agent_id)
            return True
        return False
    
    def get_memory_keys(self, agent_id: str = None) -> List[str]:
        """
        Get all available memory keys
        In shared memory, all agents see all keys
        """
        return list(self.memory.keys())
    
    def get_memory_info(self, key: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a memory entry
        """
        if agent_id not in self.agents or key not in self.memory:
            return None
        
        entry = self.memory[key]
        return {
            'key': key,
            'written_by': entry['written_by'],
            'timestamp': entry['timestamp'],
            'version': entry['version'],
            'has_value': True
        }
    
    def delete_key(self, key: str, agent_id: str) -> bool:
        """
        Delete a key from shared memory
        """
        if agent_id not in self.agents:
            return False
        
        if key in self.memory:
            del self.memory[key]
            self.log_access(agent_id, 'delete', key, success=True)
            return True
        
        self.log_access(agent_id, 'delete', key, success=False)
        return False
    
    def _get_next_version(self, key: str) -> int:
        """
        Get the next version number for a key
        """
        if key in self.memory:
            return self.memory[key]['version'] + 1
        return 1
    
    def get_value(self, key: str, agent_id: str) -> Optional[Any]:
        """
        Get just the value without metadata
        """
        entry = self.read(key, agent_id)
        if entry and isinstance(entry, dict) and 'value' in entry:
            return entry['value']
        return entry
    
    def list_agents(self) -> List[str]:
        """
        Get list of all registered agents
        """
        return self.agents.copy()
    
    def get_agent_activity(self, agent_id: str) -> Dict[str, Any]:
        """
        Get activity summary for a specific agent
        """
        if agent_id not in self.agents:
            return {}
        
        agent_logs = self.get_access_log(agent_id)
        reads = len([log for log in agent_logs if log['operation'] == 'read'])
        writes = len([log for log in agent_logs if log['operation'] == 'write'])
        
        return {
            'agent_id': agent_id,
            'total_reads': reads,
            'total_writes': writes,
            'total_operations': len(agent_logs),
            'memory_type': 'SharedMemory'
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get overall memory usage statistics
        """
        total_operations = len(self.access_log)
        successful_operations = len([log for log in self.access_log if log['success']])
        success_rate = successful_operations / total_operations if total_operations > 0 else 0.0
        
        reads = len([log for log in self.access_log if log['operation'] == 'read'])
        writes = len([log for log in self.access_log if log['operation'] == 'write'])
        deletes = len([log for log in self.access_log if log['operation'] == 'delete'])
        
        return {
            'total_keys': len(self.memory),
            'total_agents': len(self.agents),
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': success_rate,
            'operation_breakdown': {
                'reads': reads,
                'writes': writes,
                'deletes': deletes
            },
            'memory_type': 'SharedMemory'
        }
    
    def clear_memory(self) -> bool:
        """
        Clear all memory contents
        """
        self.memory.clear()
        self.access_log.clear()
        return True
