# CollabArena Memory Module

## Overview

The Memory Module provides different memory architectures for multi-agent collaboration in CollabArena. It implements three distinct memory paradigms as outlined in the research proposal:

- **Shared Memory**: All agents have full read/write access to shared memory space
- **Isolated Memory**: Each agent has private memory that others cannot access  
- **RBAC Memory**: Role-based access control with permissions and access restrictions

## Architecture

```
MemoryModule/
├── __init__.py                 # Module exports
├── base_memory.py             # Abstract base class defining memory interface
├── memory_manager.py          # Manager class coordinating different memory types
├── shared_memory.py           # Shared memory implementation
├── isolated_memory.py         # Isolated memory implementation  
├── rbac_memory.py            # Role-based access control memory
└── short_term_memory.py      # Short-term memory with size limits
```

## Key Classes

### BaseMemory (Abstract)
Defines the core interface that all memory implementations must follow:

```python
class BaseMemory(ABC):
    @abstractmethod
    def read(self, key: str, agent_id: str) -> Optional[Any]
    
    @abstractmethod  
    def write(self, key: str, value: Any, agent_id: str) -> bool
    
    @abstractmethod
    def register_agent(self, agent_id: str) -> bool
```

### MemoryManager
Provides unified interface and factory pattern for different memory types:

```python
# Create different memory managers
shared_manager = MemoryManager(mode="shared")
isolated_manager = MemoryManager(mode="isolated") 
rbac_manager = MemoryManager(mode="rbac")

# Unified operations
manager.register_agent("agent_01")
manager.write("key", "value", "agent_01")
value = manager.read("key", "agent_01")
```

### SharedMemory
All registered agents can read and write to shared memory space:

- ✅ **Complete information sharing** - all agents see all data
- ✅ **Simple coordination** - easy data exchange
- ❌ **No privacy** - all data is visible to all agents
- ❌ **Potential conflicts** - concurrent writes need management

**Use Cases**: Small teams, brainstorming, complete transparency required

### IsolatedMemory  
Each agent has private memory space that others cannot access:

- ✅ **Data privacy** - agents have private memory spaces
- ✅ **No interference** - agents cannot access each other's data
- ❌ **Limited collaboration** - harder to share information
- ❌ **Potential silos** - information may not flow between agents

**Use Cases**: Privacy requirements, independent work phases, parallel processing

### RBACMemory
Role-based access control with granular permissions:

- ✅ **Flexible permissions** - fine-grained access control
- ✅ **Role-based security** - permissions based on agent roles
- ✅ **Scalable governance** - supports complex organizational structures
- ❌ **Configuration complexity** - requires role and permission setup

**Use Cases**: Enterprise environments, hierarchical teams, sensitive data

## Memory Features

### Access Logging & Audit Trail
All memory operations are logged for analysis and debugging:

```python
# Get access logs
all_logs = memory_manager.get_access_log()
agent_logs = memory_manager.get_access_log("agent_01")

# Log entries contain:
{
    'agent_id': 'agent_01',
    'operation': 'read',  # or 'write', 'delete'
    'key': 'data_key',
    'success': True,
    'timestamp': datetime.now()
}
```

### Memory Statistics
Comprehensive statistics for monitoring and analysis:

```python
stats = memory_manager.get_memory_stats()
# Returns:
{
    'memory_mode': 'shared',
    'total_keys': 5,
    'registered_agents': 3,
    'total_reads': 15,
    'total_writes': 8,
    'successful_operations': 22,
    'total_operations': 23,
    'success_rate': 0.956
}
```

### Versioning & Metadata
Memory entries include metadata for tracking:

```python
# Memory entries stored with metadata
{
    'value': actual_data,
    'written_by': 'agent_01',
    'timestamp': datetime.now(),
    'version': 1
}
```

## Agent Integration

Agents can seamlessly work with any memory type:

```python
from src.MemoryModule import MemoryManager
from src.agent import Agent

# Create memory-enabled agent
memory_manager = MemoryManager(mode="shared")
agent = Agent("analyst_01", "Problem Analyst", prompt, memory_manager)

# Agent automatically gets memory capabilities
agent.store_memory("findings", "Analysis complete")
data = agent.retrieve_memory("findings")
context = agent.get_memory_context()  # For LLM prompts
```

## RBAC Permissions

The RBAC memory supports fine-grained permission control:

### Default Roles
- **admin**: Full access (read, write, delete, admin)
- **researcher**: Read and write access
- **validator**: Read and write access  
- **editor**: Read, write, and delete access
- **viewer**: Read-only access
- **coordinator**: Read, write, and admin access

### Custom Permissions
```python
# Grant specific permissions
rbac_manager.grant_permission("sensitive_data", "agent_01", "read")
rbac_manager.revoke_permission("sensitive_data", "agent_01", "write")

# Create custom roles
rbac_memory.create_role("analyst", {Permission.READ, Permission.WRITE})
```

## Performance Characteristics

| Memory Type | Read Complexity | Write Complexity | Scalability | Use Case |
|-------------|-----------------|------------------|-------------|----------|
| **Shared**  | O(1)           | O(1)             | Medium      | Small teams, full transparency |
| **Isolated** | O(1)          | O(1)             | High        | Privacy, parallel processing |
| **RBAC**    | O(1)           | O(1)             | High        | Enterprise, role-based access |

## Usage Examples

### Basic Memory Operations
```python
from src.MemoryModule import MemoryManager

# Create manager
manager = MemoryManager(mode="shared")

# Register agents
manager.register_agent("agent_01")
manager.register_agent("agent_02")

# Basic operations
manager.write("project_status", "In Progress", "agent_01")
status = manager.read("project_status", "agent_02")
print(f"Status: {status}")
```

### RBAC Example
```python
# Create RBAC memory
rbac_manager = MemoryManager(mode="rbac")

# Register with roles
rbac_manager.register_agent("admin_01", "admin")
rbac_manager.register_agent("researcher_01", "researcher")
rbac_manager.register_agent("viewer_01", "viewer")

# Admin can write sensitive data
rbac_manager.write("classified", "Top secret", "admin_01")

# Researcher cannot access
data = rbac_manager.read("classified", "researcher_01")  # Returns None

# Grant specific access
rbac_manager.grant_permission("classified", "researcher_01", "read")
data = rbac_manager.read("classified", "researcher_01")  # Now works
```

### Memory Mode Switching
```python
# Start with shared memory
manager = MemoryManager(mode="shared")
manager.write("data", "test", "agent_01")

# Switch to isolated (with data preservation attempt)
manager.switch_mode("isolated", preserve_data=True)

# Switch to RBAC
manager.switch_mode("rbac")
```

## Research Applications

This memory module directly supports the CollabArena research questions:

### RQ1: Memory Architecture Impact
- Compare shared vs isolated vs RBAC memory effects on:
  - Task success rate
  - Error frequency  
  - Collaboration efficiency
  - Agent performance metrics

### RQ2: Communication-Memory Interaction
- Analyze how memory type affects:
  - Message volume and patterns
  - Coordination overhead
  - Solution coherence
  - Information flow

### RQ3: Human-AI Trust
- Evaluate memory transparency effects on:
  - Human trust metrics
  - Perceived system reliability
  - Audit trail comprehension
  - Privacy concerns

## Testing

Run the comprehensive test suite:

```bash
python test_memory_system.py
```

Tests cover:
- ✅ Shared memory read/write operations
- ✅ Isolated memory privacy enforcement  
- ✅ RBAC permission and role management
- ✅ Agent-memory integration
- ✅ Access logging and statistics
- ✅ Memory manager functionality

## Future Extensions

Planned enhancements for the memory module:

1. **Adaptive Memory**: Dynamic memory allocation based on usage patterns
2. **Memory Persistence**: Save/load memory state to disk
3. **Memory Compression**: Automatic cleanup of old or unused data
4. **Memory Encryption**: Encrypted storage for sensitive data
5. **Memory Synchronization**: Distributed memory across multiple nodes
6. **Memory Analytics**: Advanced analytics and pattern detection

## Integration Notes

The memory module integrates seamlessly with:
- **Communication Module**: Stores message history and context
- **Agent System**: Provides memory-aware agent capabilities  
- **Experiment Framework**: Enables memory architecture comparisons
- **Audit System**: Comprehensive logging for research analysis

This memory architecture provides the foundation for systematic evaluation of memory effects on multi-agent collaboration as outlined in the CollabArena research proposal.
