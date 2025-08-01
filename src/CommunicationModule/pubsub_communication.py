from typing import Dict, List, Set

from .base_communicator import BaseCommunicator
from ..message import Message




class PubSubCommunicator(BaseCommunicator):
    """Publish-Subscribe communication with topic-based messaging"""
    
    def __init__(self):
        super().__init__()
        self.message_queues: Dict[str, List[Message]] = {}
        self.topics: Dict[str, Set[str]] = {}  # topic -> set of subscribed agent_ids
    
    def register_agent(self, agent) -> bool:
        """Register an agent and create their message queue"""
        agent_id = agent.get_id()
        if agent_id not in self.agents:
            self.agents[agent_id] = agent
            self.message_queues[agent_id] = []
            return True
        return False
    
    def send(self, message: Message) -> bool:
        """Publish message to all subscribers of the topic"""
        try:
            # Extract topic from your Message structure
            topic = self._get_topic_from_message(message)
            
            if topic in self.topics:
                subscribers = self.topics[topic]
                for subscriber_id in subscribers:
                    if subscriber_id != message.agent_id:  # Don't send to sender (using agent_id)
                        self.message_queues[subscriber_id].append(message)
                
                self.message_log.append(message)
                return True
            else:
                print(f"No subscribers for topic: {topic}")
                return False
        except Exception as e:
            print(f"Error publishing message: {e}")
            return False
    
    def receive(self, agent_id: str) -> List[Message]:
        """Get messages from agent's subscription queue"""
        if agent_id not in self.message_queues:
            return []
        
        # Return and clear the agent's message queue
        messages = self.message_queues[agent_id].copy()
        self.message_queues[agent_id].clear()
        return messages
    
    def subscribe(self, agent_id: str, topic: str) -> bool:
        """Subscribe agent to a topic"""
        if agent_id not in self.agents:
            return False
        
        if topic not in self.topics:
            self.topics[topic] = set()
        
        self.topics[topic].add(agent_id)
        return True
    
    def unsubscribe(self, agent_id: str, topic: str) -> bool:
        """Unsubscribe agent from a topic"""
        if topic in self.topics and agent_id in self.topics[topic]:
            self.topics[topic].remove(agent_id)
            if not self.topics[topic]:  # Remove empty topic
                del self.topics[topic]
            return True
        return False
    
    def _get_topic_from_message(self, message: Message) -> str:
        """
        Extract topic from your Message structure
        Your Message class stores topic in metadata
        """
        # First try to get topic from metadata
        if hasattr(message, 'metadata') and message.metadata:
            topic = message.metadata.get('topic')
            if topic:
                return topic
        
        # Fallback to message_type if no topic in metadata
        if hasattr(message, 'message_type'):
            return message.message_type
        
        # Default topic
        return 'general'
    
    def get_active_topics(self) -> List[str]:
        """Get list of all active topics with subscribers"""
        return list(self.topics.keys())
    
    def get_subscribers(self, topic: str) -> Set[str]:
        """Get all subscribers for a specific topic"""
        return self.topics.get(topic, set()).copy()
    
    def get_agent_subscriptions(self, agent_id: str) -> List[str]:
        """Get all topics that an agent is subscribed to"""
        subscribed_topics = []
        for topic, subscribers in self.topics.items():
            if agent_id in subscribers:
                subscribed_topics.append(topic)
        return subscribed_topics