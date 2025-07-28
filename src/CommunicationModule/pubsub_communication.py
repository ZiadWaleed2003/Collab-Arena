from datetime import datetime
from typing import Dict, List, Set, Optional
from ..message import Message


class PubSubCommunicator:
    """
    Publication/Subscription communication system where agents subscribe to topics
    and receive messages published to those topics
    """
    def __init__(self):
        self.message_counter = 0
        self.message_queues: Dict[str, List[Message]] = {}  # agent_id -> list of messages
        self.topics: Dict[str, Set[str]] = {}  # topic -> set of subscribed agent_ids
        self.all_messages: List[Message] = []  # For conversation history
        self.registered_agents: List[str] = []
        self.agent_subscriptions: Dict[str, Set[str]] = {}  # agent_id -> set of topics
    
    def register_agent(self, agent_id: str):
        """Register an agent for pub-sub communication"""
        if agent_id not in self.registered_agents:
            self.registered_agents.append(agent_id)
            self.message_queues[agent_id] = []
            self.agent_subscriptions[agent_id] = set()
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent and remove from all subscriptions"""
        if agent_id in self.registered_agents:
            self.registered_agents.remove(agent_id)
            
            # Remove from all topic subscriptions
            if agent_id in self.agent_subscriptions:
                for topic in self.agent_subscriptions[agent_id].copy():
                    self.unsubscribe(agent_id, topic)
                del self.agent_subscriptions[agent_id]
            
            # Remove message queue
            if agent_id in self.message_queues:
                del self.message_queues[agent_id]
    
    def send(self, message: Message):
        """
        Send a message to all subscribers of the message's topic
        Topic is determined from message metadata
        """
        topic = message.metadata.get('topic', 'default')
        
        # Deliver to all subscribers of this topic
        if topic in self.topics:
            for subscriber_id in self.topics[topic]:
                self._deliver_to_agent(subscriber_id, message)
        
        # Add to conversation history
        self.all_messages.append(message)
    
    def publish_message(self, agent_id: str, agent_role: str, content: str, 
                       topic: str, message_type: str = "response", 
                       metadata: Dict = None) -> str:
        """Publish a message to a specific topic"""
        self.message_counter += 1
        message_id = f"msg_{self.message_counter:04d}"
        
        # Add topic to metadata
        pub_metadata = metadata or {}
        pub_metadata.update({
            'topic': topic,
            'communication_type': 'pubsub'
        })
        
        message = Message(
            id=message_id,
            agent_id=agent_id,
            agent_role=agent_role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=pub_metadata
        )
        
        self.send(message)
        return message_id
    
    def receive(self, agent_id: str) -> List[Message]:
        """Get new messages for an agent (consume messages from queue)"""
        if agent_id not in self.message_queues:
            self.register_agent(agent_id)
        
        messages = self.message_queues[agent_id].copy()
        self.message_queues[agent_id].clear()
        return messages
    
    def peek_messages(self, agent_id: str) -> List[Message]:
        """Get messages for an agent without consuming them"""
        if agent_id not in self.message_queues:
            self.register_agent(agent_id)
        
        return self.message_queues[agent_id].copy()
    
    def subscribe(self, agent_id: str, topic: str):
        """Subscribe an agent to a topic"""
        # Ensure agent is registered
        if agent_id not in self.registered_agents:
            self.register_agent(agent_id)
        
        # Add topic if it doesn't exist
        if topic not in self.topics:
            self.topics[topic] = set()
        
        # Subscribe agent to topic
        self.topics[topic].add(agent_id)
        self.agent_subscriptions[agent_id].add(topic)
    
    def unsubscribe(self, agent_id: str, topic: str):
        """Unsubscribe an agent from a topic"""
        if topic in self.topics and agent_id in self.topics[topic]:
            self.topics[topic].remove(agent_id)
            
            # Remove topic if no subscribers left
            if not self.topics[topic]:
                del self.topics[topic]
        
        if agent_id in self.agent_subscriptions and topic in self.agent_subscriptions[agent_id]:
            self.agent_subscriptions[agent_id].remove(topic)
    
    def get_subscriptions(self, agent_id: str) -> Set[str]:
        """Get all topics an agent is subscribed to"""
        if agent_id not in self.agent_subscriptions:
            return set()
        return self.agent_subscriptions[agent_id].copy()
    
    def get_topic_subscribers(self, topic: str) -> Set[str]:
        """Get all agents subscribed to a topic"""
        if topic not in self.topics:
            return set()
        return self.topics[topic].copy()
    
    def get_all_topics(self) -> List[str]:
        """Get list of all available topics"""
        return list(self.topics.keys())
    
    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all messages in an agent's queue (without consuming)"""
        return self.peek_messages(agent_id)
    
    def get_new_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get and clear new messages for an agent (consume messages)"""
        return self.receive(agent_id)
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages from the system - maintains blackboard interface"""
        return self.all_messages.copy()
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history for LLM prompts"""
        if not self.all_messages:
            return "No previous messages."
        
        history = "=== CONVERSATION HISTORY ===\n"
        for msg in self.all_messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            topic = msg.metadata.get('topic', 'default')
            
            # Get subscribers for this topic at time of message
            subscribers = self.get_topic_subscribers(topic)
            subscribers_str = ', '.join(subscribers) if subscribers else 'none'
            
            history += f"[{timestamp}] {msg.agent_role} ({msg.agent_id}) -> TOPIC[{topic}] -> [{subscribers_str}]:\n{msg.content}\n\n"
        
        return history
    
    def post_message(self, agent_id: str, agent_role: str, content: str, 
                    message_type: str = "response", metadata: Dict = None) -> str:
        """Post a message (maintains blackboard interface) - publishes to 'default' topic"""
        return self.publish_message(agent_id, agent_role, content, 'default', message_type, metadata)
    
    def clear(self):
        """Clear all messages from the system"""
        self.all_messages.clear()
        self.message_counter = 0
        for agent_id in self.message_queues:
            self.message_queues[agent_id].clear()
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agents"""
        return self.registered_agents.copy()
    
    def create_topic(self, topic: str):
        """Create a new topic (topics are created automatically on first subscription)"""
        if topic not in self.topics:
            self.topics[topic] = set()
    
    def delete_topic(self, topic: str):
        """Delete a topic and unsubscribe all agents"""
        if topic in self.topics:
            # Unsubscribe all agents from this topic
            for agent_id in self.topics[topic].copy():
                self.unsubscribe(agent_id, topic)
            del self.topics[topic]
    
    def get_topic_message_count(self, topic: str) -> int:
        """Get count of messages published to a specific topic"""
        count = 0
        for msg in self.all_messages:
            if msg.metadata.get('topic') == topic:
                count += 1
        return count
    
    def get_messages_by_topic(self, topic: str) -> List[Message]:
        """Get all messages published to a specific topic"""
        return [msg for msg in self.all_messages if msg.metadata.get('topic') == topic]
    
    def _deliver_to_agent(self, agent_id: str, message: Message):
        """Internal method to deliver message to specific agent"""
        if agent_id not in self.message_queues:
            self.register_agent(agent_id)
        self.message_queues[agent_id].append(message)
