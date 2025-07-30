from datetime import datetime
from typing import Dict, List
from ..message import Message


class Blackboard:
    """
    Blackboard communication system where all agents can read and write messages
    """
    def __init__(self):
        self.messages: List[Message] = []
        self.message_counter = 0
    
    def post_message(self, agent_id: str, agent_role: str, content: str, 
                    message_type: str = "response", metadata: Dict = None) -> str:
        """Post a message to the blackboard"""
        self.message_counter += 1
        message_id = f"msg_{self.message_counter:04d}"
        
        message = Message(
            id=message_id,
            agent_id=agent_id,
            agent_role=agent_role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        return message_id
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages from the blackboard"""
        return self.messages.copy()
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history for LLM prompts"""
        if not self.messages:
            return "No previous messages."
        
        history = "=== CONVERSATION HISTORY ===\n"
        for msg in self.messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            history += f"[{timestamp}] {msg.agent_role} ({msg.agent_id}):\n{msg.content}\n\n"
        
        return history
    
    def clear(self):
        """Clear all messages from the blackboard"""
        self.messages.clear()
        self.message_counter = 0