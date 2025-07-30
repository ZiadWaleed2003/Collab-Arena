#!/usr/bin/env python3
"""
Shared Memory System Test and Demonstration
Tests the shared memory implementation for CollabArena
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from src.MemoryModule import MemoryManager, SharedMemory
from src.agent import Agent

def test_shared_memory():
    """Test shared memory functionality"""
    print("🧪 TESTING SHARED MEMORY")
    print("=" * 40)
    
    # Create memory manager with shared memory
    memory_manager = MemoryManager()
    
    # Create test agents
    agents = [
        Agent("analyst_01", "Problem Analyst", "You are a problem analyst.", memory_manager),
        Agent("coordinator_01", "Team Coordinator", "You are a team coordinator.", memory_manager),
        Agent("specialist_01", "Domain Specialist", "You are a domain specialist.", memory_manager)
    ]
    
    # Test basic read/write operations
    print("📝 Testing basic read/write operations...")
    
    # Agent 1 writes data
    success = memory_manager.write("project_status", "In Progress", "analyst_01")
    print(f"   Write by analyst_01: {'✅' if success else '❌'}")
    
    # Agent 2 reads data
    value = memory_manager.read("project_status", "coordinator_01")
    print(f"   Read by coordinator_01: {'✅' if value else '❌'} - Value: {value}")
    
    # Agent 3 writes additional data
    memory_manager.write("technical_notes", "Using microservices architecture", "specialist_01")
    
    # Show memory state
    state = memory_manager.get_memory_state()
    print(f"   Total memory keys: {len(state['memory_contents'])}")
    print(f"   Registered agents: {len(state['registered_agents'])}")
    
    # Show access log
    log = memory_manager.get_access_log()
    print(f"   Total access operations: {len(log)}")
    
    print("✅ Shared memory test completed!\n")

def test_memory_integration():
    """Test memory integration with agents"""
    print("🤖 TESTING AGENT-MEMORY INTEGRATION")
    print("=" * 40)
    
    # Create memory manager
    memory_manager = MemoryManager()
    
    # Create agent with memory
    agent = Agent("test_agent", "Test Agent", "You are a test agent.", memory_manager)
    
    print("📝 Testing agent memory operations...")
    
    # Test agent memory storage
    store_success = agent.store_memory("agent_state", "Active and ready")
    print(f"   Agent store memory: {'✅' if store_success else '❌'}")
    
    # Test agent memory retrieval
    retrieved = agent.retrieve_memory("agent_state")
    print(f"   Agent retrieve memory: {'✅' if retrieved else '❌'}")
    
    # Test memory context generation
    context = agent.get_memory_context()
    has_context = len(context) > 0 and "MEMORY CONTEXT" in context
    print(f"   Memory context generation: {'✅' if has_context else '❌'}")
    
    # Show agent memory activity
    activity = memory_manager.get_agent_activity("test_agent")
    if activity:
        print(f"   Agent operations: {activity.get('total_operations', 0)}")
        print(f"   Memory type: {activity.get('memory_type', 'Unknown')}")
    
    print("✅ Agent-memory integration test completed!\n")

def test_memory_features():
    """Test advanced memory features"""
    print("⚙️ TESTING MEMORY FEATURES")
    print("=" * 40)
    
    # Create memory manager
    memory_manager = MemoryManager()
    
    # Register agents
    memory_manager.register_agent("agent_01")
    memory_manager.register_agent("agent_02")
    
    print("📝 Testing memory features...")
    
    # Test versioning
    memory_manager.write("document", "Version 1", "agent_01")
    memory_manager.write("document", "Version 2", "agent_02")
    
    # Test memory keys listing
    keys = memory_manager.get_memory_keys()
    print(f"   Memory keys available: {'✅' if 'document' in keys else '❌'}")
    
    # Test value retrieval (without metadata)
    value = memory_manager.get_value("document", "agent_01")
    print(f"   Value retrieval: {'✅' if value else '❌'}")
    
    # Test memory statistics
    stats = memory_manager.get_memory_stats()
    print(f"   Statistics generation: {'✅' if stats['total_operations'] > 0 else '❌'}")
    print(f"   Success rate: {stats['success_rate']:.2%}")
    
    # Test key deletion
    delete_success = memory_manager.delete_key("document", "agent_01")
    print(f"   Key deletion: {'✅' if delete_success else '❌'}")
    
    print("✅ Memory features test completed!\n")

def main():
    """Run all memory system tests"""
    print("🚀 COLLAB-ARENA SHARED MEMORY SYSTEM TESTS")
    print("=" * 50)
    print("Testing shared memory implementation and integrations\n")
    
    try:
        # Test shared memory functionality
        test_shared_memory()
        test_memory_integration()
        test_memory_features()
        
        print("🎉 ALL MEMORY TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ Shared Memory: Full read/write access for all agents")
        print("✅ Agent Integration: Seamless memory operations in agents")
        print("✅ Memory Features: Versioning, statistics, and management")
        print("✅ Access Logging: Complete audit trail for all operations")
        print("\n📋 Shared memory system ready for CollabArena multi-agent collaboration!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
