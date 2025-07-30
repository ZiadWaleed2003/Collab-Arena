from typing import Dict, List
from ..message import Message
from .base_communicator import BaseCommunicator

class DirectMessenger(BaseCommunicator):
    """Direct messaging between agents with individual message queues"""
    
    def __init__(self):
        super().__init__()
        self.message_queues: Dict[str, List[Message]] = {}
    
    def register_agent(self, agent) -> bool:
        """Register an agent and create their message queue"""
        agent_id = getattr(agent, 'id', str(agent))
        if agent_id not in self.agents:
            self.agents[agent_id] = agent
            self.message_queues[agent_id] = []
            return True
        return False
    
    def send(self, message: Message) -> bool:
        """Send direct message to specific recipient"""
        try:
            if message.recipient_id in self.message_queues:
                self.message_queues[message.recipient_id].append(message)
                self.message_log.append(message)
                return True
            else:
                print(f"Recipient {message.recipient_id} not found")
                return False
        except Exception as e:
            print(f"Error sending direct message: {e}")
            return False
    
    def receive(self, agent_id: str) -> List[Message]:
        """Get messages from agent's personal queue"""
        if agent_id not in self.message_queues:
            return []
        
        # Return and clear the agent's message queue
        messages = self.message_queues[agent_id].copy()
        self.message_queues[agent_id].clear()
        return messages
