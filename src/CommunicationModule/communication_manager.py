from enum import Enum
from typing import List, Optional
from .blackboard import Blackboard
from src.message import Message
from .direct_communication import DirectMessenger

class CommunicationMode(Enum):
    """Enumeration for different communication modes"""
    BLACKBOARD = "blackboard"
    DIRECT = "direct"
    PUBSUB = "pubsub"


class CommunicationManager:
    """Factory pattern manager for different communication modes"""
    
    def __init__(self, mode: CommunicationMode, shared_log = None):
        self.mode = mode
        # self.shared_log = shared_log or SharedLogDB()
        
        # Create instances of all concrete communicators
        self.blackboard_impl = Blackboard()
        self.direct_impl = DirectMessenger()
        # self.pubsub_impl = PubSubCommunicator()
        
        # Set current communicator based on mode
        self.current_communicator = self.create_communicator(mode)
    
    def create_communicator(self, mode: CommunicationMode):
        """Factory method to get the appropriate communicator"""
        if mode == CommunicationMode.BLACKBOARD:
            return self.blackboard_impl
        elif mode == CommunicationMode.DIRECT:
            return self.direct_impl
        elif mode == CommunicationMode.PUBSUB:
            return self.pubsub_impl
        else:
            raise ValueError(f"Unsupported communication mode: {mode}")
    
    def register_agent(self, agent) -> bool:
        """Register agent with current communicator"""
        return self.current_communicator.register_agent(agent)
    
    def send(self, message: Message) -> bool:
        """Send message using current communicator and log it"""
        success = self.current_communicator.send(message=message
            # agent_id=message.agent_id, 
            # agent_role=message.agent_role, 
            # content=message.content, 
            # message_type=message.message_type, 
            # metadata=message.metadata)
        # if success:
        #     self._log_message(message
        )
        return success
    
    def receive(self, agent_id: str) -> List[Message]:
        """Receive messages for agent using current communicator"""
        return self.current_communicator.receive(agent_id)
    
    def subscribe(self, agent_id: str, topic: str) -> bool:
        """Subscribe to topic (only works for PubSub mode)"""
        if self.mode == CommunicationMode.PUBSUB:
            return self.pubsub_impl.subscribe(agent_id, topic)
        else:
            print(f"Subscribe operation not supported in {self.mode.value} mode")
            return False
    
    def unsubscribe(self, agent_id: str, topic: str) -> bool:
        """Unsubscribe from topic (only works for PubSub mode)"""
        if self.mode == CommunicationMode.PUBSUB:
            return self.pubsub_impl.unsubscribe(agent_id, topic)
        else:
            print(f"Unsubscribe operation not supported in {self.mode.value} mode")
            return False
    
    # def _log_message(self, message: Message):
    #     """Private method to log messages to shared database"""
    #     self.shared_log.log_message(message)


def create_message(
    sender_id: str,
    sender_role: str,
    content: str,
    recipient_id: Optional[str] = None,
    topic: Optional[str] = None
) -> Message:
    """
    Utility function to create a Message object correctly.

    Args:
        sender_id: The ID of the agent sending the message.
        sender_role: The role of the sending agent.
        content: The main content of the message.
        recipient_id: The ID of the intended recipient agent (optional).
        topic: An optional topic for the message, stored in metadata.

    Returns:
        A new Message object.
    """
    # Create a metadata dictionary, including the topic if it's provided
    metadata = {}
    if topic:
        metadata['topic'] = topic

    return Message(
        agent_id=sender_id,
        agent_role=sender_role,
        content=content,
        recipient_id=recipient_id,
        metadata=metadata
    )
