from src.CommunicationModule.communication_manager import CommunicationManager, create_message
from src.clients import get_llm_client, get_llm
from src.MemoryModule.memory_manager import MemoryManager


class Agent:
    """
    Simplified agent that works with any communication protocol through CommunicationManager
    and now includes memory functionality through MemoryManager
    """
    def __init__(self, agent_id: str, role: str, system_prompt: str, memory_manager: MemoryManager = None):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.step_count = 0
        self.client = get_llm_client()
        self.model = get_llm()
        
        # Memory integration
        self.memory_manager = memory_manager or MemoryManager()
        self.memory_manager.register_agent(self.agent_id)
        
        # Original conversation context - kept for backward compatibility
        self.conversation_context = []  # Keep local context for better LLM responses
    
    def generate_response(self, problem: str, recent_messages: list) -> str:
        """
        Generate a response using LLM with context management
        Now includes memory context for enhanced decision making
        """

        print(f"[{self.agent_id}] Generating response for problem: {problem}")
        try:
            # Format recent messages into conversation history
            conversation_history = self._format_conversation_history(recent_messages)
            
            # Get relevant memory context
            memory_context = self._get_memory_context()
            
            # Combine contexts
            full_context = conversation_history
            if memory_context:
                full_context += f"\n\n=== SHARED MEMORY CONTEXT ===\n{memory_context}"
            
            # Truncate if too long
            max_history_length = 4000
            if len(full_context) > max_history_length:
                full_context = full_context[-max_history_length:]
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Problem: {problem}\n\n{full_context}\n\nProvide a concise response (max 500 words):"}
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
            
            # Store important insights in memory
            self._store_insights_to_memory(content, problem)
            
            return content.strip()
            
        except Exception as e:
            print(f"Error generating response for {self.agent_id}: {e}")
            return f"[{self.role}] I encountered an error while processing. Please try again."
    
    def act(self, comm_manager: CommunicationManager, problem: str, recipient_id: str = "all") -> str:
        """
        Agent's main action: read messages, generate response, send message
        Works with ANY communication protocol through CommunicationManager
        Now includes memory operations for persistent context
        """
        try:
            # Get new messages (communication-agnostic)
            recent_messages = comm_manager.receive(self.agent_id)
            
            # Store important messages in memory for team context
            self._store_messages_to_memory(recent_messages, problem)
            
            # Update local context (kept for backward compatibility)
            # self.conversation_context.extend(recent_messages)
            
            # Use memory-enhanced context instead of just local context
            memory_enhanced_context = self._get_enhanced_context(recent_messages)
            
            # Keep only recent context to prevent memory bloat (original logic preserved)
            # if len(self.conversation_context) > 20:
            #     self.conversation_context = self.conversation_context[-20:]
            
            # Generate response with memory-enhanced context
            response = self.generate_response(problem, memory_enhanced_context)
            
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
    
    def _get_memory_context(self) -> str:
        """Get relevant context from shared memory"""
        try:
            memory_keys = self.memory_manager.get_memory_keys()
            if not memory_keys:
                return ""
            
            context_parts = []
            for key in memory_keys[-10:]:  # Get last 10 memory entries
                value = self.memory_manager.get_value(key, self.agent_id)
                if value:
                    context_parts.append(f"{key}: {value}")
            
            return "\n".join(context_parts) if context_parts else ""
        except Exception as e:
            print(f"Error getting memory context for {self.agent_id}: {e}")
            return ""
    
    def _store_insights_to_memory(self, response_content: str, problem: str):
        """Store important insights from response to shared memory"""
        try:
            # Create a memory key based on role and timestamp
            import time
            timestamp = int(time.time())
            memory_key = f"{self.role.lower().replace(' ', '_')}_{timestamp}"
            
            # Store the insight with context
            insight_data = {
                "role": self.role,
                "agent_id": self.agent_id,
                "problem_context": problem[:200],  # First 200 chars of problem
                "insight": response_content[:500],  # First 500 chars of response
                "timestamp": timestamp
            }
            
            self.memory_manager.write(memory_key, insight_data, self.agent_id)
        except Exception as e:
            print(f"Error storing insights to memory for {self.agent_id}: {e}")
    
    def _store_messages_to_memory(self, messages: list, problem: str):
        """Store important messages to shared memory for team context"""
        try:
            if not messages:
                return
            
            # Store key messages summary
            import time
            timestamp = int(time.time())
            memory_key = f"team_messages_{timestamp}"
            
            message_summary = {
                "problem_context": problem[:200],
                "message_count": len(messages),
                "last_messages": [
                    {
                        "sender": getattr(msg, 'sender_id', 'unknown'),
                        "content": msg.content[:200] if msg.content else "",
                        "timestamp": str(getattr(msg, 'timestamp', ''))
                    }
                    for msg in messages[-3:]  # Last 3 messages
                ],
                "stored_by": self.agent_id,
                "stored_at": timestamp
            }
            
            self.memory_manager.write(memory_key, message_summary, self.agent_id)
        except Exception as e:
            print(f"Error storing messages to memory for {self.agent_id}: {e}")
    
    def _get_enhanced_context(self, recent_messages: list) -> list:
        """Get enhanced context combining recent messages with memory"""
        try:
            # Use original conversation context as fallback
            enhanced_context = list(recent_messages)
            
            # Add memory context if available
            memory_context = self._get_memory_context()
            if memory_context:
                # Create a pseudo-message with memory context
                class MemoryMessage:
                    def __init__(self, content):
                        self.content = f"[SHARED MEMORY] {content}"
                        from datetime import datetime
                        self.timestamp = datetime.now()
                
                enhanced_context.append(MemoryMessage(memory_context))
            
            return enhanced_context
        except Exception as e:
            print(f"Error getting enhanced context for {self.agent_id}: {e}")
            return recent_messages
    
    # Memory-specific methods for external use
    def store_memory(self, key: str, value: any) -> bool:
        """Store data in shared memory"""
        return self.memory_manager.write(key, value, self.agent_id)
    
    def retrieve_memory(self, key: str) -> any:
        """Retrieve data from shared memory"""
        return self.memory_manager.get_value(key, self.agent_id)
    
    def get_all_memory_keys(self) -> list:
        """Get all available memory keys"""
        return self.memory_manager.get_memory_keys()
    
    def get_memory_state(self) -> dict:
        """Get current memory state"""
        return self.memory_manager.get_memory_state()

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