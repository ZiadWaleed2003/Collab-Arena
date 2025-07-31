"""
Short Term Memory Implementation for CollabArena
Provides temporary memory storage with limited capacity and automatic cleanup
"""

from typing import List, Any, Optional
from datetime import datetime
from collections import deque


class ShortTermMemory:
    """
    Short-term memory implementation with bounded capacity.
    Automatically manages memory by removing oldest entries when capacity is exceeded.
    Ideal for storing recent events, conversations, and temporary context.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize short-term memory with specified capacity
        """
        self.history: deque = deque(maxlen=max_size)
        self.max_size: int = max_size
    
    def add_event(self, event: Any) -> None:
        """
        Add an event to short-term memory
        
        """
        # Create event entry with timestamp and metadata
        event_entry = {
            'timestamp': datetime.now(),
            'data': event,
            'event_id': len(self.history)  # Simple incremental ID
        }
        
        # Add to history (automatically removes oldest if at capacity)
        self.history.append(event_entry)
    
    def get_recent(self, limit: int) -> List[Any]:
        """
        Get the most recent events from memory
        
        """
        if limit <= 0:
            return []
        
        # Get the last 'limit' events
        recent_events = list(self.history)[-limit:]
        
        # Return just the event data, not the metadata
        return [event['data'] for event in recent_events]
    
    def get_recent_with_metadata(self, limit: int) -> List[dict]:
        """
        Get recent events with full metadata
        """
        if limit <= 0:
            return []
        
        return list(self.history)[-limit:]
    
    def clear(self) -> None:
        """
        Clear all events from short-term memory
        """
        self.history.clear()
    
    def size(self) -> int:
        """
        Get current number of events in memory
        
        """
        return len(self.history)
    
    def is_full(self) -> bool:
        """
        Check if memory is at capacity
        """
        return len(self.history) >= self.max_size
    
    def get_all_events(self) -> List[Any]:
        """
        Get all events currently in memory
        
        """
        return [event['data'] for event in self.history]
    
    def get_events_since(self, timestamp: datetime) -> List[Any]:
        """
        Get all events since a specific timestamp
        
       
        """
        filtered_events = [
            event['data'] for event in self.history
            if event['timestamp'] > timestamp
        ]
        return filtered_events
    
    def get_memory_info(self) -> dict:
        """
        Get information about the current memory state
        
        """
        if not self.history:
            return {
                'size': 0,
                'max_size': self.max_size,
                'is_full': False,
                'oldest_event': None,
                'newest_event': None,
                'utilization_percent': 0.0
            }
        
        oldest_event = self.history[0]
        newest_event = self.history[-1]
        
        return {
            'size': len(self.history),
            'max_size': self.max_size,
            'is_full': self.is_full(),
            'oldest_event': oldest_event['timestamp'],
            'newest_event': newest_event['timestamp'],
            'utilization_percent': (len(self.history) / self.max_size) * 100
        }
    
    def __str__(self) -> str:
        """String representation of the memory state"""
        return f"ShortTermMemory(size={len(self.history)}/{self.max_size})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"ShortTermMemory(history={len(self.history)} events, max_size={self.max_size})"
