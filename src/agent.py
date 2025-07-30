from src.CommunicationModule.communication_manager import CommunicationManager, create_message
from src.clients import get_llm_client, get_llm


class Agent:
    """
    Simplified agent that works with any communication protocol through CommunicationManager
    """
    def __init__(self, agent_id: str, role: str, system_prompt: str):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.step_count = 0
        self.client = get_llm_client()
        self.model = get_llm()
        self.conversation_context = []  # Keep local context for better LLM responses
    
    def generate_response(self, problem: str, recent_messages: list) -> str:
        """
        Generate a response using LLM with context management
        """

        print(f"[{self.agent_id}] Generating response for problem: {problem}")
        try:
            # Format recent messages into conversation history
            conversation_history = self._format_conversation_history(recent_messages)
            
            # Truncate if too long
            max_history_length = 4000
            if len(conversation_history) > max_history_length:
                conversation_history = conversation_history[-max_history_length:]
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Problem: {problem}\n\n{conversation_history}\n\nProvide a concise response (max 500 words):"}
                ],
                temperature=0,
            )
            
            # Extract response content safely
            content = response.choices[0].message.content

            print("="*80)
            print(f"[{self.agent_id}] Generated response: {content}")
            
            # Handle None or empty responses
            if content is None or content.strip() == "":
                return f"[{self.role}] I'm processing the problem but have no specific response at this time."
            
            return content.strip()
            
        except Exception as e:
            print(f"Error generating response for {self.agent_id}: {e}")
            return f"[{self.role}] I encountered an error while processing. Please try again."
    
    def act(self, comm_manager: CommunicationManager, problem: str, recipient_id: str = "all") -> str:
        """
        Agent's main action: read messages, generate response, send message
        Works with ANY communication protocol through CommunicationManager
        """
        try:
            # Get new messages (communication-agnostic)
            recent_messages = comm_manager.receive(self.agent_id)
            
            # Update local context
            self.conversation_context.extend(recent_messages)
            
            # Keep only recent context to prevent memory bloat
            if len(self.conversation_context) > 20:
                self.conversation_context = self.conversation_context[-20:]
            
            # Generate response
            response = self.generate_response(problem, self.conversation_context)
            
            # Ensure response is not None or empty
            if not response or response.strip() == "":
                response = f"[{self.role}] No response generated."

            
            # Send response (communication-agnostic)
            message = create_message(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                sender_role=self.role,
                topic=self._determine_topic(response),
                content=f"[{self.role}]: {response}"
            )
            
            success = comm_manager.send(message)
            return "success" if success else "failed"
            
        except Exception as e:
            print(f"Error in agent {self.agent_id} act(): {e}")
            return "error"
    
    def subscribe_to_topic(self, comm_manager: CommunicationManager, topic: str) -> bool:
        """
        Subscribe to a topic (only works in PubSub mode)
        """
        return comm_manager.subscribe(self.agent_id, topic)
    
    def send_direct_message(self, comm_manager: CommunicationManager, 
                           recipient_id: str, content: str, topic: str = "direct") -> bool:
        """
        Send a direct message to specific agent
        """
        message = create_message(
            sender_id=self.agent_id,
            sender_role=self.role,
            recipient_id=recipient_id,
            topic=topic,
            content=f"[{self.role}]: {content}"
        )
        return comm_manager.send(message)
    
    def _format_conversation_history(self, messages: list) -> str:
        """Format messages into readable conversation history"""
        if not messages:
            return "No previous messages."
        
        history = "=== RECENT MESSAGES ===\n"
        for msg in messages[-10:]:  # Only show last 10 messages
            try:
                timestamp = msg.timestamp.strftime("%H:%M:%S")
                content = msg.content if msg.content else "[No content]"
                history += f"[{timestamp}] {content}\n"
            except Exception as e:
                history += f"[Error formatting message: {e}]\n"
        
        return history
    
    def _determine_topic(self, response_content: str) -> str:
        """
        Simple topic determination based on content and role
        """
        # Handle None or empty response content
        if not response_content:
            return "general"
        
        # Ensure response_content is a string
        if not isinstance(response_content, str):
            response_content = str(response_content)
        
        content_lower = response_content.lower()
        
        # Role-based topic mapping
        if "Problem Analyst" in self.role:
            if any(word in content_lower for word in ["analysis", "breakdown", "components"]):
                return "analysis"
            
        elif "Team Coordinator" in self.role:
            if any(word in content_lower for word in ["next steps", "action", "timeline"]):
                return "coordination"
                
        elif "Domain Specialist" in self.role:
            if any(word in content_lower for word in ["technical", "algorithm", "method"]):
                return "technical"
                
        elif "Solution Implementer" in self.role:
            if any(word in content_lower for word in ["implement", "code", "execute"]):
                return "implementation"
        
        # Default topic
        return "general"