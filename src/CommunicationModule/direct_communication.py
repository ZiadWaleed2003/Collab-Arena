from datetime import datetime
from typing import Dict, List, Optional
from ..message import Message


class DirectCommunication:
    """
    Direct peer-to-peer communication system where agents communicate directly
    Maintains the same interface as Blackboard for easy swapping
    """
    def __init__(self):
        self.message_counter = 0
        self.agent_mailboxes: Dict[str, List[Message]] = {}
        self.all_messages: List[Message] = []  # For conversation history
        self.registered_agents: List[str] = []
    
    def register_agent(self, agent_id: str):
        """Register an agent for direct communication"""
        if agent_id not in self.registered_agents:
            self.registered_agents.append(agent_id)
            self.agent_mailboxes[agent_id] = []
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.registered_agents:
            self.registered_agents.remove(agent_id)
            if agent_id in self.agent_mailboxes:
                del self.agent_mailboxes[agent_id]
    
    def post_message(self, agent_id: str, agent_role: str, content: str, 
                    message_type: str = "response", metadata: Dict = None) -> str:
        """Post a message (broadcast to all agents) - maintains blackboard interface"""
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
        
        # In direct communication, broadcast to all other agents
        self._broadcast_to_all(message, exclude_sender=agent_id)
        self.all_messages.append(message)
        return message_id
    
    def send_direct_message(self, sender_id: str, sender_role: str, 
                           recipient_id: str, content: str, 
                           message_type: str = "direct", metadata: Dict = None) -> str:
        """Send a direct message to a specific agent"""
        self.message_counter += 1
        message_id = f"msg_{self.message_counter:04d}"
        
        # Add recipient info to metadata
        direct_metadata = metadata or {}
        direct_metadata.update({
            'recipient_id': recipient_id,
            'communication_type': 'direct'
        })
        
        message = Message(
            id=message_id,
            agent_id=sender_id,
            agent_role=sender_role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=direct_metadata
        )
        
        # Deliver to specific recipient
        self._deliver_to_agent(recipient_id, message)
        self.all_messages.append(message)
        return message_id
    
    def send_to_multiple(self, sender_id: str, sender_role: str, 
                        recipient_ids: List[str], content: str, 
                        message_type: str = "multicast", metadata: Dict = None) -> str:
        """Send a message to multiple specific agents"""
        self.message_counter += 1
        message_id = f"msg_{self.message_counter:04d}"
        
        # Add recipients info to metadata
        multi_metadata = metadata or {}
        multi_metadata.update({
            'recipient_ids': recipient_ids,
            'communication_type': 'multicast'
        })
        
        message = Message(
            id=message_id,
            agent_id=sender_id,
            agent_role=sender_role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=multi_metadata
        )
        
        # Deliver to specified recipients
        for recipient_id in recipient_ids:
            self._deliver_to_agent(recipient_id, message)
        
        self.all_messages.append(message)
        return message_id
    
    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all messages in an agent's mailbox"""
        if agent_id not in self.agent_mailboxes:
            self.register_agent(agent_id)
        return self.agent_mailboxes[agent_id].copy()
    
    def get_new_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get and clear new messages for an agent (consume messages)"""
        if agent_id not in self.agent_mailboxes:
            self.register_agent(agent_id)
        
        messages = self.agent_mailboxes[agent_id].copy()
        self.agent_mailboxes[agent_id].clear()
        return messages
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages from the system - maintains blackboard interface"""
        return self.all_messages.copy()
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history for LLM prompts - maintains blackboard interface"""
        if not self.all_messages:
            return "No previous messages."
        
        history = "=== CONVERSATION HISTORY ===\n"
        for msg in self.all_messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            
            # Add communication type info for direct messages
            comm_type = msg.metadata.get('communication_type', 'broadcast')
            if comm_type == 'direct':
                recipient = msg.metadata.get('recipient_id', 'unknown')
                history += f"[{timestamp}] {msg.agent_role} ({msg.agent_id}) -> {recipient} [DIRECT]:\n{msg.content}\n\n"
            elif comm_type == 'multicast':
                recipients = msg.metadata.get('recipient_ids', [])
                recipients_str = ', '.join(recipients)
                history += f"[{timestamp}] {msg.agent_role} ({msg.agent_id}) -> [{recipients_str}] [MULTICAST]:\n{msg.content}\n\n"
            else:
                history += f"[{timestamp}] {msg.agent_role} ({msg.agent_id}) [BROADCAST]:\n{msg.content}\n\n"
        
        return history
    
    def clear(self):
        """Clear all messages from the system - maintains blackboard interface"""
        self.all_messages.clear()
        self.message_counter = 0
        for agent_id in self.agent_mailboxes:
            self.agent_mailboxes[agent_id].clear()
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agents"""
        return self.registered_agents.copy()
    
    def _broadcast_to_all(self, message: Message, exclude_sender: str = None):
        """Internal method to broadcast message to all registered agents"""
        for agent_id in self.registered_agents:
            if exclude_sender and agent_id == exclude_sender:
                continue
            self._deliver_to_agent(agent_id, message)
    
    def _deliver_to_agent(self, agent_id: str, message: Message):
        """Internal method to deliver message to specific agent"""
        if agent_id not in self.agent_mailboxes:
            self.register_agent(agent_id)
        self.agent_mailboxes[agent_id].append(message)
