from src.CommunicationModule.blackboard import Blackboard
from src.CommunicationModule.direct_communication import DirectCommunication
from src.clients import get_llm_client, get_llm
from typing import Union


class Agent:
    """
    Base agent that communicates through either Blackboard or Direct Communication using LLM calls
    """
    def __init__(self, agent_id: str, role: str, system_prompt: str):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.step_count = 0
        self.client = get_llm_client()
        self.model = get_llm()

    
    def generate_response(self, problem: str, conversation_history: str) -> str:
        """
        Generate a response using LLM with context length management
        """
        # Truncate conversation history if too long to prevent context overflow
        max_history_length = 4000  # Reserve space for problem, system prompt, and response
        if len(conversation_history) > max_history_length:
            # Keep the beginning (problem statement) and recent messages
            lines = conversation_history.split('\n')
            # Keep first 20 lines (problem setup) and last 50 lines (recent conversation)
            if len(lines) > 70:
                truncated_history = '\n'.join(lines[:20] + ['...[conversation truncated]...'] + lines[-50:])
            else:
                truncated_history = conversation_history[:max_history_length]
        else:
            truncated_history = conversation_history
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Problem: {problem}\n\n{truncated_history}\n\nProvide a concise response (max 500 words):"}
            ],
            temperature=0,
            max_tokens=500  # Reduce max tokens to keep responses shorter
        )
        return response.choices[0].message.content
        
    
    def act(self, communication_module: Union[Blackboard, DirectCommunication], problem: str) -> str:
        """
        Agent's main action: read messages, generate response, post message
        Works with both Blackboard and DirectCommunication modules
        """
        # Register agent if using direct communication
        if isinstance(communication_module, DirectCommunication):
            communication_module.register_agent(self.agent_id)
        
        # Read conversation history (both modules support this method)
        conversation_history = communication_module.get_conversation_history()
        
        # Generate response using LLM
        response = self.generate_response(problem, conversation_history)
        
        # Post response (both modules support this method)
        message_id = communication_module.post_message(
            agent_id=self.agent_id,
            agent_role=self.role,
            content=response,
            message_type="response"
        )
        
        return message_id
    
    def send_direct_message(self, communication_module: DirectCommunication, 
                           recipient_id: str, content: str) -> str:
        """
        Send a direct message to another agent (only works with DirectCommunication)
        """
        if not isinstance(communication_module, DirectCommunication):
            raise ValueError("Direct messaging only supported with DirectCommunication module")
        
        return communication_module.send_direct_message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=recipient_id,
            content=content
        )
    
    def get_my_messages(self, communication_module: DirectCommunication) -> list:
        """
        Get messages specifically for this agent (only works with DirectCommunication)
        """
        if not isinstance(communication_module, DirectCommunication):
            raise ValueError("Agent mailboxes only supported with DirectCommunication module")
        
        return communication_module.get_messages_for_agent(self.agent_id)