"""
RBAC Memory Implementation for CollabArena
Provides role-based access control for memory operations
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
from .base_memory import BaseMemory


class AccessLevel(Enum):
    """Access levels for RBAC memory system"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class RBACMemory(BaseMemory):
    """
    Role-Based Access Control memory implementation
    Controls memory access based on agent roles and permissions
    """
    
    def __init__(self):
        super().__init__()
        self.memory: Dict[str, Any] = {}
        self.role_permissions: Dict[str, Set[AccessLevel]] = {}
        self.agent_roles: Dict[str, str] = {}
        self.protected_keys: Set[str] = set()  # Keys requiring special permissions
        
        # Initialize default role permissions
        self._setup_default_roles()
    
    def _setup_default_roles(self):
        """Setup default role permissions"""
        self.role_permissions = {
            "Problem Analyst": {AccessLevel.READ, AccessLevel.WRITE},
            "Team Coordinator": {AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE},
            "Domain Specialist": {AccessLevel.READ, AccessLevel.WRITE},
            "Solution Implementer": {AccessLevel.READ, AccessLevel.WRITE},
            "Admin": {AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN},
            "Guest": {AccessLevel.READ}
        }
    
    def register_agent(self, agent_id: str, role: str = "Guest") -> bool:
        """
        Register an agent with a specific role
        
        Args:
            agent_id: ID of the agent to register
            role: Role to assign to the agent
            
        Returns:
            True if registration successful, False otherwise
        """
        if agent_id not in self.agents:
            self.agents.append(agent_id)
            self.agent_roles[agent_id] = role
            self.on_agent_registered(agent_id)
            return True
        return False
    
    def set_agent_role(self, agent_id: str, new_role: str, admin_agent_id: str) -> bool:
        """
        Change an agent's role (requires admin privileges)
        
        Args:
            agent_id: Agent whose role to change
            new_role: New role to assign
            admin_agent_id: Agent performing the role change (must have admin access)
            
        Returns:
            True if role change successful, False otherwise
        """
        if not self._has_permission(admin_agent_id, AccessLevel.ADMIN):
            self.log_access(admin_agent_id, 'role_change', agent_id, success=False)
            return False
        
        if agent_id in self.agent_roles and new_role in self.role_permissions:
            old_role = self.agent_roles[agent_id]
            self.agent_roles[agent_id] = new_role
            self.log_access(admin_agent_id, 'role_change', 
                          f"{agent_id}: {old_role} -> {new_role}", success=True)
            return True
        
        return False
    
    def add_role_permission(self, role: str, permission: AccessLevel, admin_agent_id: str) -> bool:
        """
        Add permission to a role (requires admin privileges)
        """
        if not self._has_permission(admin_agent_id, AccessLevel.ADMIN):
            return False
        
        if role not in self.role_permissions:
            self.role_permissions[role] = set()
        
        self.role_permissions[role].add(permission)
        self.log_access(admin_agent_id, 'permission_add', f"{role}: {permission.value}", success=True)
        return True
    
    def remove_role_permission(self, role: str, permission: AccessLevel, admin_agent_id: str) -> bool:
        """
        Remove permission from a role (requires admin privileges)
        """
        if not self._has_permission(admin_agent_id, AccessLevel.ADMIN):
            return False
        
        if role in self.role_permissions and permission in self.role_permissions[role]:
            self.role_permissions[role].discard(permission)
            self.log_access(admin_agent_id, 'permission_remove', f"{role}: {permission.value}", success=True)
            return True
        
        return False
    
    def protect_key(self, key: str, admin_agent_id: str) -> bool:
        """
        Mark a key as protected (requires admin access to modify)
        """
        if not self._has_permission(admin_agent_id, AccessLevel.ADMIN):
            return False
        
        self.protected_keys.add(key)
        self.log_access(admin_agent_id, 'protect_key', key, success=True)
        return True
    
    def unprotect_key(self, key: str, admin_agent_id: str) -> bool:
        """
        Remove protection from a key
        """
        if not self._has_permission(admin_agent_id, AccessLevel.ADMIN):
            return False
        
        self.protected_keys.discard(key)
        self.log_access(admin_agent_id, 'unprotect_key', key, success=True)
        return True
    
    def read(self, key: str, agent_id: str) -> Optional[Any]:
        """
        Read data from RBAC memory with permission check
        """
        if not self._has_permission(agent_id, AccessLevel.READ):
            self.log_access(agent_id, 'read', key, success=False)
            return None
        
        if key in self.memory:
            value = self.memory[key]
            self.log_access(agent_id, 'read', key, success=True)
            return value
        else:
            self.log_access(agent_id, 'read', key, success=False)
            return None
    
    def write(self, key: str, value: Any, agent_id: str) -> bool:
        """
        Write data to RBAC memory with permission check
        """
        if not self._has_permission(agent_id, AccessLevel.WRITE):
            self.log_access(agent_id, 'write', key, success=False)
            return False
        
        # Check if key is protected and requires admin access
        if key in self.protected_keys and not self._has_permission(agent_id, AccessLevel.ADMIN):
            self.log_access(agent_id, 'write', key, success=False)
            return False
        
        # Write the value with metadata
        self.memory[key] = {
            'value': value,
            'written_by': agent_id,
            'timestamp': datetime.now(),
            'version': self._get_next_version(key),
            'access_level': 'protected' if key in self.protected_keys else 'normal'
        }
        
        self.log_access(agent_id, 'write', key, success=True)
        return True
    
    def delete_key(self, key: str, agent_id: str) -> bool:
        """
        Delete a key from RBAC memory with permission check
        """
        if not self._has_permission(agent_id, AccessLevel.DELETE):
            self.log_access(agent_id, 'delete', key, success=False)
            return False
        
        # Check if key is protected and requires admin access
        if key in self.protected_keys and not self._has_permission(agent_id, AccessLevel.ADMIN):
            self.log_access(agent_id, 'delete', key, success=False)
            return False
        
        if key in self.memory:
            del self.memory[key]
            self.protected_keys.discard(key)  # Remove protection if key is deleted
            self.log_access(agent_id, 'delete', key, success=True)
            return True
        
        return False
    
    def get_memory_keys(self, agent_id: str) -> List[str]:
        """
        Get accessible memory keys based on agent permissions
        """
        if not self._has_permission(agent_id, AccessLevel.READ):
            return []
        
        # Admins see all keys, others see only non-admin-only keys
        if self._has_permission(agent_id, AccessLevel.ADMIN):
            return list(self.memory.keys())
        else:
            # Filter out keys that might be admin-only based on content or protection
            accessible_keys = []
            for key in self.memory.keys():
                if key not in self.protected_keys or self._has_permission(agent_id, AccessLevel.ADMIN):
                    accessible_keys.append(key)
            return accessible_keys
    
    def get_agent_permissions(self, agent_id: str) -> Set[AccessLevel]:
        """
        Get permissions for a specific agent
        """
        if agent_id not in self.agent_roles:
            return set()
        
        role = self.agent_roles[agent_id]
        return self.role_permissions.get(role, set())
    
    def get_role_info(self, role: str) -> Dict[str, Any]:
        """
        Get information about a specific role
        """
        return {
            'role': role,
            'permissions': [perm.value for perm in self.role_permissions.get(role, set())],
            'agents': [agent_id for agent_id, agent_role in self.agent_roles.items() if agent_role == role]
        }
    
    def get_all_roles(self) -> List[str]:
        """
        Get all available roles
        """
        return list(self.role_permissions.keys())
    
    def get_protected_keys(self, agent_id: str) -> List[str]:
        """
        Get list of protected keys (admin access required)
        """
        if self._has_permission(agent_id, AccessLevel.ADMIN):
            return list(self.protected_keys)
        else:
            return []  # Non-admin agents can't see protected keys list
    
    def get_rbac_stats(self) -> Dict[str, Any]:
        """
        Get RBAC system statistics
        """
        role_distribution = {}
        for role in self.role_permissions.keys():
            role_distribution[role] = len([a for a, r in self.agent_roles.items() if r == role])
        
        return {
            'total_agents': len(self.agents),
            'total_roles': len(self.role_permissions),
            'protected_keys': len(self.protected_keys),
            'role_distribution': role_distribution,
            'memory_entries': len(self.memory),
            'access_log_entries': len(self.access_log)
        }
    
    def _has_permission(self, agent_id: str, required_permission: AccessLevel) -> bool:
        """
        Check if agent has required permission
        """
        if agent_id not in self.agent_roles:
            return False
        
        role = self.agent_roles[agent_id]
        role_permissions = self.role_permissions.get(role, set())
        
        return required_permission in role_permissions
    
    def _get_next_version(self, key: str) -> int:
        """Get next version number for a key"""
        if key in self.memory:
            return self.memory[key].get('version', 0) + 1
        return 1
    
    def get_memory_info(self, key: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a memory entry with RBAC checks
        """
        if not self._has_permission(agent_id, AccessLevel.READ):
            return None
        
        if key not in self.memory:
            return None
        
        # Check if key is protected and agent doesn't have admin access
        if key in self.protected_keys and not self._has_permission(agent_id, AccessLevel.ADMIN):
            return None
        
        entry = self.memory[key]
        return {
            'key': key,
            'written_by': entry['written_by'],
            'timestamp': entry['timestamp'],
            'version': entry['version'],
            'access_level': entry.get('access_level', 'normal'),
            'is_protected': key in self.protected_keys,
            'has_value': True
        }
    
    def __str__(self) -> str:
        """String representation of RBAC memory"""
        return f"RBACMemory(agents={len(self.agents)}, roles={len(self.role_permissions)}, entries={len(self.memory)})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"RBACMemory(agents={len(self.agents)}, roles={list(self.role_permissions.keys())}, protected_keys={len(self.protected_keys)})"
