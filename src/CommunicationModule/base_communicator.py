from abc import ABC, abstractmethod
from typing import Dict, List

from message import Message


class BaseCommunicator(ABC):
    """Abstract base class for all communication implementations"""
    
    def __init__(self):
        self.agents: Dict[str, object] = {}
        self.message_log: List[Message] = []
    
    @abstractmethod
    def register_agent(self, agent) -> bool:
        """Register an agent with the communicator"""
        pass
    
    @abstractmethod
    def send_message(self, message: Message) -> bool:
        """Send a message"""
        pass
    
    @abstractmethod
    def receive_message(self, agent_id: str) -> List[Message]:
        """Receive messages for a specific agent"""
        pass




