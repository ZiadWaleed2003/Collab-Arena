from src.CommunicationModule.blackboard import Blackboard
from src.CommunicationModule.direct_communication import DirectCommunication
from src.CommunicationModule.pubsub_communication import PubSubCommunicator
from src.MemoryModule.memory_manager import MemoryManager
from src.clients import get_llm_client, get_llm
from typing import Union, Optional


class Agent:
    """
    Base agent that communicates through different protocols and uses memory system
    """
    def __init__(self, agent_id: str, role: str, system_prompt: str, memory_manager: Optional[MemoryManager] = None):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.step_count = 0
        self.client = get_llm_client()
        self.model = get_llm()
        self.memory_manager = memory_manager
        
        # Register with memory if available
        if self.memory_manager:
            self.memory_manager.register_agent(self.agent_id)

    def store_memory(self, key: str, value: any) -> bool:
        """
        Store data in agent's memory
        """
        if self.memory_manager is None:
            return False
        return self.memory_manager.write(key, value, self.agent_id)
    
    def retrieve_memory(self, key: str) -> any:
        """
        Retrieve data from agent's memory
        """
        if self.memory_manager is None:
            return None
        return self.memory_manager.read(key, self.agent_id)
    
    def get_memory_context(self) -> str:
        """
        Get memory context for LLM prompts
        """
        if self.memory_manager is None:
            return ""
        
        # Get some recent memory entries for context
        memory_state = self.memory_manager.get_memory_state()
        memory_contents = memory_state.get('memory_contents', {})
        
        if not memory_contents:
            return ""
        
        context = "\n=== MEMORY CONTEXT ===\n"
        for key, entry in list(memory_contents.items())[-5:]:  # Last 5 entries
            if isinstance(entry, dict) and 'value' in entry:
                context += f"{key}: {entry['value']}\n"
            else:
                context += f"{key}: {entry}\n"
        context += "========================\n"
        
        return context

    
    def generate_response(self, problem: str, conversation_history: str) -> str:
        """
        Generate a response using LLM with context length management and memory
        """
        # Get memory context
        memory_context = self.get_memory_context()
        
        # Truncate conversation history if too long to prevent context overflow
        max_history_length = 3500  # Reserve space for problem, system prompt, memory, and response
        if len(conversation_history) > max_history_length:
            lines = conversation_history.split('\n')
            if len(lines) > 70:
                truncated_history = '\n'.join(lines[:20] + ['...[conversation truncated]...'] + lines[-50:])
            else:
                truncated_history = conversation_history[:max_history_length]
        else:
            truncated_history = conversation_history
        
        # Combine all context
        full_context = f"Problem: {problem}\n\n{memory_context}{truncated_history}\n\nProvide a concise response (max 500 words):"
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": full_context}
            ],
            temperature=0,
            max_tokens=500
        )
        
        generated_response = response.choices[0].message.content
        
        # Store response in memory for future reference
        if self.memory_manager:
            response_key = f"response_{self.step_count}"
            self.store_memory(response_key, {
                'content': generated_response,
                'problem_context': problem[:200],  # Store partial problem context
                'step': self.step_count
            })
        
        return generated_response
        
    
    def act(self, communication_module: Union[Blackboard, DirectCommunication, PubSubCommunicator], problem: str) -> str:
        """
        Agent's main action: read messages, generate response, post message
        Enhanced with memory usage
        """
        # Store current problem in memory
        if self.memory_manager:
            self.store_memory("current_problem", problem)
            self.store_memory(f"step_{self.step_count}", {"action": "starting_turn"})
        
        # Register agent and handle specific communication module setup
        if isinstance(communication_module, DirectCommunication):
            communication_module.register_agent(self.agent_id)
        elif isinstance(communication_module, PubSubCommunicator):
            communication_module.register_agent(self.agent_id)
            self._setup_pubsub_subscriptions(communication_module)
        
        # Use communication-specific message retrieval
        if isinstance(communication_module, PubSubCommunicator):
            # Get messages from agent's personal queue
            new_messages = communication_module.get_new_messages_for_agent(self.agent_id)
            conversation_history = self._format_pubsub_history(new_messages, communication_module)
        elif isinstance(communication_module, DirectCommunication):
            # Get messages from agent's mailbox
            new_messages = communication_module.get_new_messages_for_agent(self.agent_id)
            conversation_history = communication_module.get_conversation_history()
        else:
            # Blackboard - get all messages
            conversation_history = communication_module.get_conversation_history()
        
        # Store conversation history in memory
        if self.memory_manager:
            self.store_memory("last_conversation", conversation_history[-1000:])  # Store last 1000 chars
        
        # Generate response using LLM
        response = self.generate_response(problem, conversation_history)
        
        # Post response using communication-specific method
        if isinstance(communication_module, PubSubCommunicator):
            # Determine appropriate topic based on agent role and response content
            topic = self._determine_topic(response)
            message_id = communication_module.publish_message(
                agent_id=self.agent_id,
                agent_role=self.role,
                content=response,
                topic=topic,
                message_type="response"
            )
        else:
            # Use generic post_message for blackboard and direct communication
            message_id = communication_module.post_message(
                agent_id=self.agent_id,
                agent_role=self.role,
                content=response,
                message_type="response"
            )
        
        # Update step count and store completion
        self.step_count += 1
        if self.memory_manager:
            self.store_memory(f"step_{self.step_count-1}", {
                "action": "completed_turn", 
                "message_id": message_id,
                "response_length": len(response)
            })
        
        return message_id
    
    def _setup_pubsub_subscriptions(self, communication_module: PubSubCommunicator):
        """Setup role-specific subscriptions for pub-sub communication"""
        # All agents subscribe to general coordination topics
        general_topics = ["problem_statements", "coordination", "final_solutions"]
        for topic in general_topics:
            communication_module.subscribe(self.agent_id, topic)
        
        # Role-specific subscriptions for relevant cross-role collaboration
        if "Problem Analyst" in self.role:
            # Analyst should see implementation plans to understand feasibility
            # and status updates to track progress
            role_specific = ["problem_breakdown", "analysis_requests", "status_updates", "implementation_plans"]
        elif "Team Coordinator" in self.role:
            # Coordinator should see all key outputs to coordinate effectively
            role_specific = ["status_updates", "team_sync", "problem_breakdown", "technical_insights", "implementation_plans"]
        elif "Domain Specialist" in self.role:
            # Specialist should see problem analysis and implementation needs
            role_specific = ["technical_insights", "expert_consultation", "problem_breakdown", "implementation_plans"]
        elif "Solution Implementer" in self.role:
            # Implementer should see technical insights and coordination updates
            role_specific = ["implementation_plans", "technical_details", "technical_insights", "status_updates"]
        else:
            role_specific = []
        
        # Subscribe to role-specific topics
        for topic in role_specific:
            communication_module.subscribe(self.agent_id, topic)
    
    def _determine_topic(self, response_content: str) -> str:
        """Determine appropriate topic based on agent role and response content"""
        # Simple keyword-based topic determination
        content_lower = response_content.lower()
        
        # Role-based topic mapping - but prioritize shared topics for collaboration
        if "Problem Analyst" in self.role:
            if any(word in content_lower for word in ["analysis", "breakdown", "components"]):
                return "problem_breakdown"  # Other agents can subscribe to this
            elif any(word in content_lower for word in ["recommend", "suggest", "next"]):
                return "coordination"  # Shared topic
        
        elif "Team Coordinator" in self.role:
            if any(word in content_lower for word in ["next steps", "action", "timeline", "assign"]):
                return "coordination"  # Shared topic - critical for coordination
            elif any(word in content_lower for word in ["status", "progress", "update"]):
                return "status_updates"
        
        elif "Domain Specialist" in self.role:
            if any(word in content_lower for word in ["technical", "algorithm", "approach", "method"]):
                return "technical_insights"
            elif any(word in content_lower for word in ["recommend", "suggest", "solution"]):
                return "coordination"  # Shared topic
        
        elif "Solution Implementer" in self.role:
            if any(word in content_lower for word in ["implement", "code", "execute", "plan"]):
                return "implementation_plans"
            elif any(word in content_lower for word in ["recommend", "suggest", "approach"]):
                return "coordination"  # Shared topic
        
        # Final solution messages - everyone should see these
        if any(word in content_lower for word in ["solution", "final", "conclusion", "result"]):
            return "final_solutions"
        
        # Default to coordination topic for better collaboration
        return "coordination"
    
    def _format_pubsub_history(self, new_messages, communication_module: PubSubCommunicator) -> str:
        """Format conversation history for pub-sub with topic context"""
        if not new_messages:
            # If no new messages, get some recent context from all messages
            all_messages = communication_module.get_all_messages()
            recent_messages = all_messages[-5:] if len(all_messages) > 5 else all_messages
            
            if not recent_messages:
                return "No previous messages."
            
            history = "=== RECENT CONVERSATION CONTEXT ===\n"
            for msg in recent_messages:
                timestamp = msg.timestamp.strftime("%H:%M:%S")
                topic = msg.metadata.get('topic', 'default')
                history += f"[{timestamp}] {msg.agent_role} on TOPIC[{topic}]:\n{msg.content}\n\n"
            return history
        
        # Format new messages received by this agent
        history = "=== NEW MESSAGES FOR YOU ===\n"
        for msg in new_messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            topic = msg.metadata.get('topic', 'default')
            history += f"[{timestamp}] {msg.agent_role} on TOPIC[{topic}]:\n{msg.content}\n\n"
        
        return history
    
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