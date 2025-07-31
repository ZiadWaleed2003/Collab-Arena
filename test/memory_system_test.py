"""
Comprehensive test suite for the Memory Module including Short-Term Memory
Tests SharedMemory, MemoryManager, and ShortTermMemory implementations
"""

import unittest
import time
from datetime import datetime, timedelta
from src.MemoryModule.memory_manager import MemoryManager
from src.MemoryModule.shared_memory import SharedMemory
from src.MemoryModule.short_term_memory import ShortTermMemory
from src.agent import Agent


class TestShortTermMemory(unittest.TestCase):
    """Test cases for ShortTermMemory implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.short_memory = ShortTermMemory(max_size=5)
    
    def test_initialization(self):
        """Test short-term memory initialization"""
        self.assertEqual(self.short_memory.max_size, 5)
        self.assertEqual(self.short_memory.size(), 0)
        self.assertFalse(self.short_memory.is_full())
        
    def test_add_event(self):
        """Test adding events to short-term memory"""
        event1 = {"type": "test", "content": "First event"}
        event2 = "Simple string event"
        
        self.short_memory.add_event(event1)
        self.short_memory.add_event(event2)
        
        self.assertEqual(self.short_memory.size(), 2)
        
        recent_events = self.short_memory.get_recent(2)
        self.assertEqual(len(recent_events), 2)
        self.assertEqual(recent_events[0], event1)
        self.assertEqual(recent_events[1], event2)
    
    def test_capacity_limit(self):
        """Test that memory respects capacity limits"""
        # Fill memory beyond capacity
        for i in range(7):
            self.short_memory.add_event(f"Event {i}")
        
        # Should only keep the last 5 events due to max_size=5
        self.assertEqual(self.short_memory.size(), 5)
        self.assertTrue(self.short_memory.is_full())
        
        recent_events = self.short_memory.get_recent(10)
        self.assertEqual(len(recent_events), 5)
        
        # Should contain events 2-6 (the last 5)
        for i, event in enumerate(recent_events):
            self.assertEqual(event, f"Event {i + 2}")
    
    def test_get_recent_with_limit(self):
        """Test getting recent events with different limits"""
        for i in range(4):
            self.short_memory.add_event(f"Event {i}")
        
        # Test various limits
        self.assertEqual(len(self.short_memory.get_recent(2)), 2)
        self.assertEqual(len(self.short_memory.get_recent(5)), 4)  # Only 4 events exist
        self.assertEqual(len(self.short_memory.get_recent(0)), 0)
        
        # Test limit larger than available
        recent = self.short_memory.get_recent(10)
        self.assertEqual(len(recent), 4)
    
    def test_clear_memory(self):
        """Test clearing short-term memory"""
        for i in range(3):
            self.short_memory.add_event(f"Event {i}")
        
        self.assertEqual(self.short_memory.size(), 3)
        
        self.short_memory.clear()
        
        self.assertEqual(self.short_memory.size(), 0)
        self.assertEqual(len(self.short_memory.get_recent(5)), 0)
        self.assertFalse(self.short_memory.is_full())
    
    def test_get_recent_with_metadata(self):
        """Test getting events with metadata"""
        event = {"test": "data"}
        self.short_memory.add_event(event)
        
        events_with_metadata = self.short_memory.get_recent_with_metadata(1)
        self.assertEqual(len(events_with_metadata), 1)
        
        event_entry = events_with_metadata[0]
        self.assertIn('timestamp', event_entry)
        self.assertIn('data', event_entry)
        self.assertIn('event_id', event_entry)
        self.assertEqual(event_entry['data'], event)
        self.assertIsInstance(event_entry['timestamp'], datetime)
    
    def test_get_events_since(self):
        """Test getting events since a specific timestamp"""
        # Add some events with time gaps
        past_time = datetime.now() - timedelta(seconds=1)
        
        self.short_memory.add_event("Old event")
        time.sleep(0.1)  # Small delay
        cutoff_time = datetime.now()
        time.sleep(0.1)  # Small delay
        self.short_memory.add_event("New event 1")
        self.short_memory.add_event("New event 2")
        
        recent_events = self.short_memory.get_events_since(cutoff_time)
        self.assertEqual(len(recent_events), 2)
        self.assertIn("New event 1", recent_events)
        self.assertIn("New event 2", recent_events)
    
    def test_memory_info(self):
        """Test getting memory information"""
        # Test empty memory
        info = self.short_memory.get_memory_info()
        self.assertEqual(info['size'], 0)
        self.assertEqual(info['max_size'], 5)
        self.assertFalse(info['is_full'])
        self.assertIsNone(info['oldest_event'])
        self.assertIsNone(info['newest_event'])
        self.assertEqual(info['utilization_percent'], 0.0)
        
        # Add some events
        self.short_memory.add_event("Event 1")
        self.short_memory.add_event("Event 2")
        
        info = self.short_memory.get_memory_info()
        self.assertEqual(info['size'], 2)
        self.assertEqual(info['max_size'], 5)
        self.assertFalse(info['is_full'])
        self.assertIsNotNone(info['oldest_event'])
        self.assertIsNotNone(info['newest_event'])
        self.assertEqual(info['utilization_percent'], 40.0)


class TestMemoryManagerWithShortTerm(unittest.TestCase):
    """Test cases for MemoryManager with short-term memory support"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.memory_manager = MemoryManager(short_term_max_size=10)
        self.agent_id1 = "test_agent_1"
        self.agent_id2 = "test_agent_2"
        
        # Register agents
        self.memory_manager.register_agent(self.agent_id1)
        self.memory_manager.register_agent(self.agent_id2)
    
    def test_agent_registration_with_short_term(self):
        """Test that agent registration creates short-term memory"""
        agent_id = "new_agent"
        success = self.memory_manager.register_agent(agent_id)
        
        self.assertTrue(success)
        
        # Should be able to use short-term memory methods
        self.assertEqual(self.memory_manager.get_short_term_memory_size(agent_id), 0)
        self.assertFalse(self.memory_manager.is_short_term_memory_full(agent_id))
    
    def test_short_term_memory_operations(self):
        """Test short-term memory operations through MemoryManager"""
        event1 = {"type": "test", "content": "Test event"}
        event2 = "Simple event"
        
        # Add events
        success1 = self.memory_manager.add_short_term_event(self.agent_id1, event1)
        success2 = self.memory_manager.add_short_term_event(self.agent_id1, event2)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        self.assertEqual(self.memory_manager.get_short_term_memory_size(self.agent_id1), 2)
        
        # Get recent events
        recent = self.memory_manager.get_recent_events(self.agent_id1, 5)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0], event1)
        self.assertEqual(recent[1], event2)
    
    def test_short_term_memory_isolation(self):
        """Test that short-term memories are isolated between agents"""
        self.memory_manager.add_short_term_event(self.agent_id1, "Agent 1 event")
        self.memory_manager.add_short_term_event(self.agent_id2, "Agent 2 event")
        
        agent1_events = self.memory_manager.get_recent_events(self.agent_id1, 5)
        agent2_events = self.memory_manager.get_recent_events(self.agent_id2, 5)
        
        self.assertEqual(len(agent1_events), 1)
        self.assertEqual(len(agent2_events), 1)
        self.assertEqual(agent1_events[0], "Agent 1 event")
        self.assertEqual(agent2_events[0], "Agent 2 event")
    
    def test_clear_short_term_memory(self):
        """Test clearing agent's short-term memory"""
        self.memory_manager.add_short_term_event(self.agent_id1, "Event to clear")
        self.assertEqual(self.memory_manager.get_short_term_memory_size(self.agent_id1), 1)
        
        success = self.memory_manager.clear_short_term_memory(self.agent_id1)
        self.assertTrue(success)
        self.assertEqual(self.memory_manager.get_short_term_memory_size(self.agent_id1), 0)
    
    def test_short_term_memory_info(self):
        """Test getting short-term memory information"""
        # Add some events
        for i in range(3):
            self.memory_manager.add_short_term_event(self.agent_id1, f"Event {i}")
        
        info = self.memory_manager.get_short_term_memory_info(self.agent_id1)
        self.assertIsNotNone(info)
        self.assertEqual(info['size'], 3)
        self.assertEqual(info['max_size'], 10)
        self.assertFalse(info['is_full'])
    
    def test_operations_with_unregistered_agent(self):
        """Test operations with unregistered agent"""
        unregistered_id = "unregistered_agent"
        
        # Should return appropriate defaults for unregistered agent
        self.assertFalse(self.memory_manager.add_short_term_event(unregistered_id, "event"))
        self.assertEqual(self.memory_manager.get_recent_events(unregistered_id, 5), [])
        self.assertEqual(self.memory_manager.get_short_term_memory_size(unregistered_id), 0)
        self.assertFalse(self.memory_manager.is_short_term_memory_full(unregistered_id))
        self.assertIsNone(self.memory_manager.get_short_term_memory_info(unregistered_id))


class TestAgentShortTermMemoryIntegration(unittest.TestCase):
    """Test cases for Agent integration with short-term memory"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.memory_manager = MemoryManager(short_term_max_size=20)
        self.agent = Agent(
            agent_id="test_agent",
            role="Test Agent",
            system_prompt="You are a test agent.",
            memory_manager=self.memory_manager
        )
    
    def test_agent_short_term_memory_methods(self):
        """Test agent's short-term memory methods"""
        event = {"type": "test", "content": "Test event for agent"}
        
        # Test adding event
        success = self.agent.add_to_short_term_memory(event)
        self.assertTrue(success)
        
        # Test getting recent events
        recent = self.agent.get_recent_short_term_events(5)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0], event)
        
        # Test memory size
        self.assertEqual(self.agent.get_short_term_memory_size(), 1)
        
        # Test memory info
        info = self.agent.get_short_term_memory_info()
        self.assertEqual(info['size'], 1)
        self.assertEqual(info['max_size'], 20)
    
    def test_agent_memory_context_with_short_term(self):
        """Test that memory context includes short-term events"""
        # Add some events to short-term memory
        self.agent.add_to_short_term_memory({
            "type": "insight",
            "content": "Important insight",
            "timestamp": int(time.time())
        })
        self.agent.add_to_short_term_memory({
            "type": "action",
            "content": "Performed action",
            "timestamp": int(time.time())
        })
        
        # Get memory context
        context = self.agent._get_memory_context()
        
        # Should include short-term memory section
        self.assertIn("RECENT PERSONAL EVENTS", context)
        self.assertIn("INSIGHT", context)
        self.assertIn("ACTION", context)
    
    def test_automatic_short_term_memory_storage(self):
        """Test that insights are automatically stored in short-term memory"""
        # This would normally be called during response generation
        problem = "Test problem"
        response = "Test response with insights"
        
        initial_size = self.agent.get_short_term_memory_size()
        
        # Call the method that stores insights
        self.agent._store_insights_to_memory(response, problem)
        
        # Should have added an event to short-term memory
        new_size = self.agent.get_short_term_memory_size()
        self.assertEqual(new_size, initial_size + 1)
        
        # Check the stored event
        recent_events = self.agent.get_recent_short_term_events(1)
        self.assertEqual(len(recent_events), 1)
        
        event = recent_events[0]
        self.assertEqual(event['type'], 'insight')
        self.assertIn('content', event)
        self.assertIn('problem', event)


class TestSharedMemoryIntegration(unittest.TestCase):
    """Test cases for existing shared memory functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.shared_memory = SharedMemory()
        self.agent_id1 = "agent1"
        self.agent_id2 = "agent2"
        
        # Register agents
        self.shared_memory.register_agent(self.agent_id1)
        self.shared_memory.register_agent(self.agent_id2)
    
    def test_shared_memory_basic_operations(self):
        """Test basic shared memory operations"""
        key = "test_key"
        value = {"data": "test_value", "type": "test"}
        
        # Write operation
        success = self.shared_memory.write(key, value, self.agent_id1)
        self.assertTrue(success)
        
        # Read operation by same agent
        result = self.shared_memory.read(key, self.agent_id1)
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], value)
        self.assertEqual(result['written_by'], self.agent_id1)
        
        # Read operation by different agent (should work in shared memory)
        result2 = self.shared_memory.read(key, self.agent_id2)
        self.assertIsNotNone(result2)
        self.assertEqual(result2['value'], value)
    
    def test_memory_statistics(self):
        """Test memory statistics functionality"""
        # Write some data
        for i in range(5):
            self.shared_memory.write(f"key_{i}", f"value_{i}", self.agent_id1)
        
        stats = self.shared_memory.get_memory_stats()
        self.assertGreaterEqual(stats['total_entries'], 5)
        self.assertGreaterEqual(stats['successful_operations'], 5)
        self.assertGreaterEqual(stats['success_rate'], 90)  # Should be high


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestShortTermMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManagerWithShortTerm))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentShortTermMemoryIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSharedMemoryIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.2f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
