"""
LangGraph-based Coordination Engine with Persistent State Tracking and Memory Integration

This module implements the complete orchestration workflow using LangGraph with:
- Full state persistence across all nodes
- Memory tracking of all orchestration decisions
- Learning from human feedback patterns
- Error recovery and resilience
- Cross-session learning capabilities
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

# Import existing components
import sys
import os
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.agent import Agent
from src.MemoryModule.memory_manager import MemoryManager
from src.CommunicationModule.communication_manager import CommunicationManager
from .data_models import OrchestratorResponse
from pydantic import ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestrationState(TypedDict):
    """Complete state schema with orchestration memory tracking"""
    
    # Input from user
    task_config: Dict[str, Any]
    user_preferences: Dict[str, Any]
    
    # Agent planning & creation
    agent_plan: List[Dict[str, Any]]
    created_agents: List[Any]  # Agent instances
    agent_creation_reasoning: List[str]  # Why each agent was created
    agent_modifications_history: List[Dict[str, Any]]  # Track all changes made
    
    # Memory & Communication managers
    memory_manager: Any
    communication_manager: Any
    
    # Human interaction tracking
    human_feedback: Optional[str]
    human_feedback_history: List[Dict[str, Any]]  # All human interactions
    needs_modifications: bool
    human_approved: bool
    approval_iterations: int  # How many rounds of feedback
    
    # Orchestration execution tracking
    current_step: str
    execution_phase: str  # "planning", "agent_creation", "human_approval", "execution"
    step_timestamps: Dict[str, str]  # When each step occurred
    orchestration_decisions: List[Dict[str, Any]]  # Decision log
    
    # Performance & metrics tracking
    agent_performance_metrics: Dict[str, Any]
    task_progress_milestones: List[Dict[str, Any]]
    orchestration_effectiveness: Dict[str, Any]
    
    # Error handling & recovery
    error_message: Optional[str]
    error_history: List[Dict[str, Any]]
    recovery_attempts: int


class LangGraphCoordinationEngine:
    """
    LangGraph-based Coordination Engine with in-memory state tracking
    """
    
    def __init__(self):
        self.memory = MemorySaver()  # In-memory storage for current session
        self.workflow = StateGraph(OrchestrationState)
        self.app = None
        self.learning_patterns = {
            "human_feedback_patterns": []
        }
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup the complete LangGraph workflow with all nodes"""
        
        # Add all nodes based on the diagram
        self.workflow.add_node("orchestrator", self._orchestrator_node)
        self.workflow.add_node("creating_agents", self._creating_agents_node)
        self.workflow.add_node("human_interaction", self._human_interaction_node)
        self.workflow.add_node("conditional_check", self._conditional_node)
        self.workflow.add_node("send_back_modifications", self._send_back_modifications_node)
        self.workflow.add_node("start_working", self._start_working_node)
        
        # Define the workflow edges based on diagram
        self.workflow.add_edge(START, "orchestrator")
        self.workflow.add_edge("orchestrator", "creating_agents")
        self.workflow.add_edge("creating_agents", "human_interaction")
        self.workflow.add_edge("human_interaction", "conditional_check")
        
        # Conditional routing
        self.workflow.add_conditional_edges(
            "conditional_check",
            self._should_modify,
            {
                "modify": "send_back_modifications",
                "approved": "start_working"
            }
        )
        
        self.workflow.add_edge("send_back_modifications", "orchestrator")
        self.workflow.add_edge("start_working", END)
        
        # Compile with checkpointing for persistence
        self.app = self.workflow.compile(checkpointer=self.memory)
    
    # LLM-Powered Orchestrator Methods
    
    def _create_orchestrator_agent(self) -> Agent:
        """Create the orchestrator agent with LLM capabilities for intelligent analysis"""

        orchestrator_system_prompt  = "".join([
                                                    "You are an intelligent Orchestration Agent responsible for analyzing tasks and designing optimal multi-agent architectures.\n",
                                                    "Your primary responsibilities:\n",
                                                    "1. Analyze user task descriptions and requirements\n",
                                                    "2. Determine task complexity and type\n",
                                                    "3. Design optimal agent team compositions\n",
                                                    "4. Select appropriate memory and communication strategies\n",
                                                    "5. Provide detailed reasoning for all decisions\n",
                                                    "\n",
                                                    "Key capabilities:\n",
                                                    "- Deep understanding of multi-agent system design\n",
                                                    "- Task complexity assessment\n",
                                                    "- Agent role specialization\n",
                                                    "- Communication pattern optimization\n",
                                                    "- Memory architecture selection\n",
                                                    "\n",
                                                    "Analysis Framework:\n",
                                                    "- Task Classification: coding, data_analysis, research, writing, design, general\n",
                                                    "- Complexity Levels: low, medium, high\n",
                                                    "- Agent Roles: Based on task requirements (be creative and specific)\n",
                                                    "- Memory Modes: shared, isolated, rbac\n",
                                                    "- Communication: direct, blackboard, pubsub\n",
                                                    "\n",
                                                    "Always provide structured analysis with confidence scores and clear reasoning.\n",
                                                    "Be creative with agent roles - don't just use generic templates, design roles that fit the specific task.\n",
                                                    "Use the following JSON structure for your response:\n",
                                                    "Response Format:\n",
                                                    "Provide your analysis in this JSON structure:\n",
                                                    "```json",
                                                    "{\n"
                                                    '    "task_analysis": {\n'
                                                    '        "task_type": "string",\n'
                                                    '        "complexity_level": "low/medium/high",\n'
                                                    '        "key_requirements": ["req1", "req2", "..."],\n'
                                                    '        "reasoning": "detailed analysis reasoning",\n'
                                                    '        "confidence_score": 0.0\n'
                                                    "    },\n"
                                                    '    "agent_plan": [\n'
                                                    "        {\n"
                                                    '            "agent_id": "unique_id",\n'
                                                    '            "role": "specific_role_name",\n'
                                                    '            "capabilities": ["capability1", "capability2"],\n'
                                                    '            "reasoning": "why this agent is needed",\n'
                                                    '            "priority": "high/medium/low"\n'
                                                    "        }\n"
                                                    "    ],\n"
                                                    '    "recommended_config": {\n'
                                                    '        "memory_mode": "shared/isolated/rbac",\n'
                                                    '        "communication_mode": "direct/blackboard/pubsub",\n'
                                                    '        "reasoning": "why these modes are optimal"\n'
                                                    "    }\n"
                                                    "}\n",
                                                    "Ensure your response is well-structured and detailed, with clear reasoning for each decision.\n",
                                                    "Also don't include any pleasantries or greetings, just get straight to the analysis.\n",])



        # Create orchestrator agent
        orchestrator_agent = Agent(
            agent_id="orchestrator_llm",
            role="Orchestration Analyst",
            system_prompt=orchestrator_system_prompt,
            memory_manager=None  # Orchestrator doesn't need shared memory
        )
        
        return orchestrator_agent
    
    def _create_task_analysis_prompt(self, task_config: Dict[str, Any], user_preferences: Dict[str, Any], modification_history: List[Dict[str, Any]]) -> str:
        """Create comprehensive prompt for LLM-powered task analysis"""
        
        task_description = task_config.get("task_description", "")
        environment_config = task_config.get("environment_config", {})
        
        # Build modification context if this is a revision
        modification_context = ""
        if modification_history:
            latest_modification = modification_history[-1]
            modification_context = "".join([
                                            "MODIFICATION CONTEXT:\n",
                                            f"This is a revision (iteration {len(modification_history)}).\n",
                                            "Previous human feedback:\n",
                                            f"\"{latest_modification.get('requested_changes', '')}\"\n",
                                            "\n",
                                            "Please take this feedback into account when redesigning the agent architecture."])
        
        prompt = "".join([
                        "TASK ANALYSIS REQUEST\n\n",
                        "TASK DESCRIPTION:\n",
                        f"{task_description}\n\n",
                        "USER PREFERENCES:\n",
                        f"{json.dumps(user_preferences, indent=2)}\n\n",
                        "ENVIRONMENT CONFIGURATION:\n",
                        f"{json.dumps(environment_config, indent=2)}\n\n",
                        f"{modification_context}\n",
                        "Please analyze this task and design an optimal multi-agent architecture. Consider:\n\n",
                        "1. What type of task is this and what's its complexity?\n",
                        "2. What are the key requirements and sub-tasks?\n",
                        "3. What specific agent roles would be most effective?\n",
                        "4. How should agents communicate and share memory?\n",
                        "5. What's the optimal team size and composition?\n\n",
                        "Be creative and specific with agent roles - design roles that perfectly fit this task rather than using generic templates.\n\n",
                        "Provide your analysis in the specified JSON format with detailed reasoning.\n"])


        return prompt
    
    def _parse_orchestrator_response(self, orchestrator_response: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse the LLM orchestrator response into structured data using Pydantic.
        If parsing or validation fails, it falls back to a default plan.
        """
        try:  
            
            # Still use regex to find the JSON block within the LLM's text response
            json_match = re.search(r'\{.*\}', orchestrator_response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in the LLM response.")
                
            json_str = json_match.group()
            
            # Use Pydantic to parse and validate the JSON string
            parsed_data = OrchestratorResponse.model_validate_json(json_str)
            
            # Convert Pydantic models to dictionaries for compatibility with the rest of the state
            task_analysis_dict = parsed_data.task_analysis.model_dump()
            agent_plan_list = [item.model_dump() for item in parsed_data.agent_plan]
            
            # Add memory_access field to each agent for compatibility
            for agent in agent_plan_list:
                agent["memory_access"] = "standard"
            
            # Add recommended config to the analysis dict
            recommended_config_dict = parsed_data.recommended_config.model_dump()
            task_analysis_dict["recommended_memory_mode"] = recommended_config_dict.get("memory_mode")
            task_analysis_dict["recommended_communication_mode"] = recommended_config_dict.get("communication_mode")
            task_analysis_dict["config_reasoning"] = recommended_config_dict.get("reasoning")
            
            logger.info("✅ Successfully parsed and validated LLM response with Pydantic.")
            return task_analysis_dict, agent_plan_list

        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"⚠️ Pydantic parsing/validation failed: {e}. Falling back to default plan.")
            logger.debug(f"Raw response that failed parsing: {orchestrator_response}")
            
            fallback_plan = self._get_fallback_agent_plan({"task_description": "Fallback due to parsing error."})
            fallback_analysis = {
                "task_type": "general_fallback",
                "complexity_level": "medium",
                "reasoning": f"Fallback due to parsing error: {str(e)}",
                "confidence_score": 0.5
            }
            return fallback_analysis, fallback_plan
    
    # LangGraph Node Implementations
    
    def _orchestrator_node(self, state: OrchestrationState) -> OrchestrationState:
        """
        Orchestrator Node: LLM-powered intelligent task analysis and agent planning
        TRACKS: decision-making process, analysis reasoning, patterns detected
        """
        logger.info("🎯 Orchestrator Node: AI-powered task analysis starting")
        
        # Update state tracking
        current_time = datetime.now().isoformat()
        state["current_step"] = "orchestrator"
        state["execution_phase"] = "planning"
        state["step_timestamps"]["orchestrator"] = current_time
        
        try:
            # Create orchestrator agent for intelligent analysis
            orchestrator_agent = self._create_orchestrator_agent()
            
            # Prepare analysis prompt with task and user context
            analysis_prompt = self._create_task_analysis_prompt(
                state["task_config"], 
                state["user_preferences"],
                state.get("agent_modifications_history", [])
            )
            
            # Get LLM-powered analysis and agent planning
            logger.info("🤖 Orchestrator Agent analyzing task and planning architecture...")
            orchestrator_response = orchestrator_agent.generate_response(
                problem=analysis_prompt,
                recent_messages=[]
            )
            
            # Parse orchestrator response
            task_analysis, agent_plan = self._parse_orchestrator_response(orchestrator_response)
            
            # Record orchestration decisions
            orchestration_decision = {
                "timestamp": current_time,
                "node": "orchestrator",
                "decision_type": "llm_powered_task_analysis_and_planning",
                "orchestrator_response": orchestrator_response,
                "task_type": task_analysis.get("task_type", "unknown"),
                "complexity_level": task_analysis.get("complexity_level", "medium"),
                "reasoning": task_analysis.get("reasoning", ""),
                "agent_plan_summary": f"{len(agent_plan)} agents planned",
                "llm_confidence": task_analysis.get("confidence_score", 0.8)
            }
            
            state["orchestration_decisions"].append(orchestration_decision)
            state["agent_plan"] = agent_plan
            
            logger.info(f"✅ LLM Analysis Complete: {task_analysis.get('task_type', 'Unknown')} task with {len(agent_plan)} agents planned")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "orchestrator", 
                "error": str(e),
                "recovery_action": "fallback_to_rule_based_planning"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Fallback to rule-based planning
            logger.warning(f"⚠️ LLM analysis failed: {e}. Falling back to rule-based planning.")
            agent_plan = self._get_fallback_agent_plan(state["task_config"])
            state["agent_plan"] = agent_plan
        
        return state
    
    def _creating_agents_node(self, state: OrchestrationState) -> OrchestrationState:
        """
        Creating Agents Node: Instantiate and configure agents
        TRACKS: agent creation process, configuration decisions, setup issues
        """
        logger.info("🤖 Creating Agents Node: Instantiating configured agents")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "creating_agents"
        state["execution_phase"] = "agent_creation"
        state["step_timestamps"]["creating_agents"] = current_time
        
        try:
            # Initialize managers with memory tracking (use LLM recommendations if available)
            memory_config = state["user_preferences"].get("memory_mode")
            comm_config = state["user_preferences"].get("communication_mode")
            
            # Use LLM recommendations from orchestrator if user didn't specify
            if state.get("orchestration_decisions"):
                latest_decision = state["orchestration_decisions"][-1]
                if latest_decision.get("decision_type") == "llm_powered_task_analysis_and_planning":
                    # Find the task analysis from orchestrator decisions
                    for decision in state["orchestration_decisions"]:
                        if "recommended_memory_mode" in str(decision):
                            if not memory_config:  # Only use recommendation if user didn't specify
                                memory_config = "shared"  # Default fallback
                            if not comm_config:
                                comm_config = "blackboard"  # Default fallback
                            break
            
            # Final fallbacks
            memory_config = memory_config or "shared"
            comm_config = comm_config or "blackboard"
            
            # Create memory manager with reasoning
            memory_manager = self._create_memory_manager_with_reasoning(memory_config)
            comm_manager = self._create_communication_manager_with_reasoning(comm_config)
            
            state["memory_manager"] = memory_manager
            state["communication_manager"] = comm_manager
            
            # Create agents with detailed tracking
            created_agents = []
            agent_creation_reasoning = []
            
            for i, agent_config in enumerate(state["agent_plan"]):
                try:
                    # Generate system prompt with context
                    system_prompt = self._generate_system_prompt_with_context(
                        agent_config["role"], 
                        state["task_config"]["task_description"],
                        agent_config
                    )
                    
                    # Create agent instance
                    agent = Agent(
                        agent_id=agent_config["agent_id"],
                        role=agent_config["role"],
                        system_prompt=system_prompt,
                        memory_manager=memory_manager
                    )
                    
                    created_agents.append(agent)
                    
                    # Track reasoning for this agent creation
                    creation_reasoning = {
                        "agent_id": agent_config["agent_id"],
                        "role": agent_config["role"],
                        "reasoning": agent_config.get("reasoning", ""),
                        "capabilities": agent_config.get("capabilities", []),
                        "memory_access": agent_config.get("memory_access", "standard"),
                        "creation_timestamp": current_time
                    }
                    agent_creation_reasoning.append(str(creation_reasoning))
                    
                    logger.info(f"✅ Created agent: {agent_config['agent_id']} ({agent_config['role']})")
                    
                except Exception as agent_error:
                    error_info = {
                        "timestamp": current_time,
                        "node": "creating_agents",
                        "agent_config": agent_config,
                        "error": str(agent_error)
                    }
                    state["error_history"].append(error_info)
                    logger.error(f"❌ Failed to create agent {agent_config.get('agent_id', i)}: {agent_error}")
            
            state["created_agents"] = created_agents
            state["agent_creation_reasoning"] = agent_creation_reasoning
            
            # Record orchestration decision
            orchestration_decision = {
                "timestamp": current_time,
                "node": "creating_agents",
                "decision_type": "agent_instantiation",
                "agents_created": len(created_agents),
                "memory_mode": memory_config,
                "communication_mode": comm_config,
                "creation_success_rate": len(created_agents) / len(state["agent_plan"]) if state["agent_plan"] else 0
            }
            state["orchestration_decisions"].append(orchestration_decision)
            
            logger.info(f"✅ Successfully created {len(created_agents)}/{len(state['agent_plan'])} agents")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "creating_agents",
                "error": str(e),
                "recovery_action": "partial_agent_creation"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            logger.error(f"❌ Agent creation error: {e}")
        
        return state
    
    def _human_interaction_node(self, state: OrchestrationState) -> OrchestrationState:
        """
        Human Interaction Node: Present configuration for human approval
        TRACKS: interaction history, presentation content, response patterns
        """
        logger.info("👤 Human Interaction Node: Presenting configuration for approval")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "human_interaction"
        state["execution_phase"] = "human_approval"
        state["step_timestamps"]["human_interaction"] = current_time
        
        try:
            # Generate comprehensive configuration summary
            config_summary = self._generate_configuration_summary(state)
            
            # Present to human (in real implementation, this would be UI/API call)
            human_response = self._present_to_human_with_tracking(config_summary, state)
            
            # Process and store human feedback
            feedback_processed = self._process_human_feedback(human_response, state)
            
            # Update state with human interaction
            state["human_feedback"] = human_response.get("feedback", "")
            
            human_interaction_record = {
                "timestamp": current_time,
                "iteration": state["approval_iterations"] + 1,
                "config_presented": config_summary,
                "human_response": human_response,
                "processing_result": feedback_processed
            }
            state["human_feedback_history"].append(human_interaction_record)
            state["approval_iterations"] += 1
            
            # Determine if modifications needed
            state["needs_modifications"] = feedback_processed.get("needs_modifications", False)
            state["human_approved"] = feedback_processed.get("approved", False)
            
            # Store interaction pattern for learning
            self._store_human_interaction_pattern(config_summary, human_response)
            
            # Record orchestration decision
            orchestration_decision = {
                "timestamp": current_time,
                "node": "human_interaction",
                "decision_type": "human_feedback_processing",
                "approval_iteration": state["approval_iterations"],
                "human_approved": state["human_approved"],
                "needs_modifications": state["needs_modifications"],
                "feedback_type": feedback_processed.get("feedback_type", "unknown")
            }
            state["orchestration_decisions"].append(orchestration_decision)
            
            logger.info(f"✅ Human interaction completed. Approved: {state['human_approved']}, Needs modifications: {state['needs_modifications']}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "human_interaction",
                "error": str(e),
                "recovery_action": "assume_approval"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Fallback: assume approval if human interaction fails
            state["human_approved"] = True
            state["needs_modifications"] = False
            logger.error(f"❌ Human interaction error: {e}. Assuming approval.")
        
        return state
    
    def _conditional_node(self, state: OrchestrationState) -> OrchestrationState:
        """
        Conditional Node: Evaluate if modifications are needed
        TRACKS: decision logic, routing decisions, condition evaluation
        """
        logger.info("🔀 Conditional Node: Evaluating modification requirements")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "conditional_check"
        state["step_timestamps"]["conditional_check"] = current_time
        
        try:
            # Evaluate conditions with detailed reasoning
            evaluation_result = self._evaluate_modification_conditions(state)
            
            # Record decision logic
            orchestration_decision = {
                "timestamp": current_time,
                "node": "conditional_check",
                "decision_type": "routing_evaluation",
                "human_approved": state.get("human_approved", False),
                "needs_modifications": state.get("needs_modifications", False),
                "evaluation_reasoning": evaluation_result.get("reasoning", ""),
                "next_route": "modify" if state.get("needs_modifications", False) else "approved"
            }
            state["orchestration_decisions"].append(orchestration_decision)
            
            logger.info(f"✅ Conditional evaluation: Route to {'modifications' if state.get('needs_modifications', False) else 'start working'}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "conditional_check",
                "error": str(e),
                "recovery_action": "default_to_approved"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Fallback: assume approved
            state["needs_modifications"] = False
            logger.error(f"❌ Conditional evaluation error: {e}. Defaulting to approved.")
        
        return state
    
    def _send_back_modifications_node(self, state: OrchestrationState) -> OrchestrationState:
        """
        Send Back Modifications Node: Process requested changes
        TRACKS: modification requests, implementation strategy, iteration patterns
        """
        logger.info("🔄 Send Back Modifications Node: Processing requested changes")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "send_back_modifications"
        state["step_timestamps"]["send_back_modifications"] = current_time
        
        try:
            # Process modifications with detailed tracking
            modifications = self._process_modifications_with_tracking(state)
            
            # Apply modifications to agent plan
            modified_plan = self._apply_modifications_to_plan(state["agent_plan"], modifications)
            
            # Track modification history
            modification_record = {
                "timestamp": current_time,
                "iteration": len(state["agent_modifications_history"]) + 1,
                "requested_changes": state.get("human_feedback", ""),
                "modifications_applied": modifications,
                "plan_changes": self._compare_plans(state["agent_plan"], modified_plan)
            }
            state["agent_modifications_history"].append(modification_record)
            
            # Update agent plan
            state["agent_plan"] = modified_plan
            
            # Reset approval status for next iteration
            state["human_approved"] = False
            state["needs_modifications"] = False
            
            # Record orchestration decision
            orchestration_decision = {
                "timestamp": current_time,
                "node": "send_back_modifications",
                "decision_type": "modification_processing",
                "modifications_count": len(modifications),
                "iteration_number": len(state["agent_modifications_history"]),
                "modification_types": [mod.get("type", "unknown") for mod in modifications]
            }
            state["orchestration_decisions"].append(orchestration_decision)
            
            logger.info(f"✅ Processed {len(modifications)} modifications for iteration {len(state['agent_modifications_history'])}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "send_back_modifications",
                "error": str(e),
                "recovery_action": "minimal_modifications"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            logger.error(f"❌ Modification processing error: {e}")
        
        return state
    
    def _start_working_node(self, state: OrchestrationState) -> OrchestrationState:
        """
        Start Working Node: Finalize configuration and begin execution
        TRACKS: final configuration, transition to execution, baseline metrics
        """
        logger.info("🚀 Start Working Node: Finalizing configuration and starting execution")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "start_working"
        state["execution_phase"] = "execution"
        state["step_timestamps"]["start_working"] = current_time
        
        try:
            # Finalize configuration with tracking
            final_config = self._finalize_configuration_with_tracking(state)
            
            # Record baseline metrics
            baseline_metrics = self._establish_baseline_metrics(state)
            state["agent_performance_metrics"] = baseline_metrics
            
            # Record final orchestration decision
            orchestration_decision = {
                "timestamp": current_time,
                "node": "start_working",
                "decision_type": "execution_initiation",
                "final_agent_count": len(state.get("created_agents", [])),
                "total_approval_iterations": state.get("approval_iterations", 0),
                "configuration_hash": hash(str(final_config)),
                "orchestration_effectiveness": self._calculate_orchestration_effectiveness(state)
            }
            state["orchestration_decisions"].append(orchestration_decision)
            
            # Add milestone for execution start
            milestone = {
                "timestamp": current_time,
                "milestone": "orchestration_completed",
                "details": "Configuration approved and agents ready for execution"
            }
            state["task_progress_milestones"].append(milestone)
            
            logger.info(f"✅ Orchestration completed successfully. {len(state.get('created_agents', []))} agents ready for execution.")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "start_working",
                "error": str(e),
                "recovery_action": "proceed_with_current_config"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            logger.error(f"❌ Start working error: {e}. Proceeding with current configuration.")
        
        return state
    
    # Routing Function
    
    def _should_modify(self, state: OrchestrationState) -> str:
        """Determine routing based on human feedback"""
        if state.get("needs_modifications", False):
            return "modify"
        return "approved"
    
    # Helper Methods for Legacy Support and Fallbacks
    
    def _detect_task_type_fallback(self, description: str) -> str:
        """Fallback task type detection when LLM analysis fails"""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["code", "programming", "software", "development", "debug"]):
            return "coding"
        elif any(keyword in description_lower for keyword in ["data", "analysis", "statistics", "visualization", "dataset"]):
            return "data_analysis"
        elif any(keyword in description_lower for keyword in ["research", "information", "study", "investigate", "explore"]):
            return "research"
        elif any(keyword in description_lower for keyword in ["write", "document", "report", "content", "article"]):
            return "writing"
        elif any(keyword in description_lower for keyword in ["design", "creative", "visual", "ui", "ux"]):
            return "design"
        else:
            return "general"
    
    # Memory and Communication Manager Creation
    
    def _create_memory_manager_with_reasoning(self, memory_config: str) -> MemoryManager:
        """Create memory manager with configuration reasoning"""
        try:
            if memory_config == "rbac":
                return MemoryManager(memory_type="rbac")
            elif memory_config == "isolated":
                return MemoryManager(memory_type="isolated")
            else:
                return MemoryManager(memory_type="shared")
        except Exception:
            # Fallback to shared memory
            return MemoryManager(memory_type="shared")
    
    def _create_communication_manager_with_reasoning(self, comm_config: str) -> CommunicationManager:
        """Create communication manager with configuration reasoning"""
        try:
            return CommunicationManager(protocol=comm_config)
        except Exception:
            # Fallback to blackboard
            return CommunicationManager(protocol="blackboard")
    
    def _generate_system_prompt_with_context(self, role: str, task_description: str, agent_config: Dict[str, Any]) -> str:
        """Generate contextual system prompt for agent"""
        capabilities = agent_config.get("capabilities", [])
        
        prompt = f"""You are an AI agent with the role of {role}.

Your primary responsibilities include: {', '.join(capabilities)}

Task Context: {task_description}

Agent Configuration:
- Agent ID: {agent_config['agent_id']}
- Role: {role}
- Capabilities: {capabilities}
- Memory Access: {agent_config.get('memory_access', 'standard')}

Guidelines:
1. Stay focused on your role and capabilities
2. Collaborate effectively with other agents
3. Provide clear, actionable outputs
4. Use memory systems to maintain context
5. Communicate through designated channels

Remember: You are part of a multi-agent system working towards a common goal. Your expertise in {role} is crucial for success.
"""
        return prompt
    
    # Human Interaction Methods
    
    def _generate_configuration_summary(self, state: OrchestrationState) -> Dict[str, Any]:
        """Generate comprehensive configuration summary for human review"""
        return {
            "task_description": state["task_config"].get("task_description", ""),
            "agent_count": len(state.get("agent_plan", [])),
            "agent_roles": [agent.get("role", "Unknown") for agent in state.get("agent_plan", [])],
            "memory_mode": state["user_preferences"].get("memory_mode", "shared"),
            "communication_mode": state["user_preferences"].get("communication_mode", "blackboard"),
            "estimated_complexity": "Medium",  # Would be calculated
            "orchestration_decisions": len(state.get("orchestration_decisions", [])),
            "approval_iteration": state.get("approval_iterations", 0) + 1
        }
    
    def _present_to_human_with_tracking(self, config_summary: Dict[str, Any], state: OrchestrationState) -> Dict[str, Any]:
        """Present configuration to human with tracking"""
        # In real implementation, this would be API/UI call
        # For now, simulate human response
        return {
            "feedback": "Configuration looks good",
            "approved": True,
            "modifications": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def _process_human_feedback(self, human_response: Dict[str, Any], state: OrchestrationState) -> Dict[str, Any]:
        """Process and interpret human feedback"""
        return {
            "approved": human_response.get("approved", True),
            "needs_modifications": not human_response.get("approved", True),
            "feedback_type": "approval" if human_response.get("approved", True) else "modification_request",
            "processing_timestamp": datetime.now().isoformat()
        }
    
    # Modification Processing
    
    def _evaluate_modification_conditions(self, state: OrchestrationState) -> Dict[str, Any]:
        """Evaluate conditions for modifications"""
        return {
            "reasoning": f"Human approved: {state.get('human_approved', False)}, Needs modifications: {state.get('needs_modifications', False)}",
            "decision": "modify" if state.get("needs_modifications", False) else "approved"
        }
    
    def _process_modifications_with_tracking(self, state: OrchestrationState) -> List[Dict[str, Any]]:
        """Process requested modifications with detailed tracking"""
        # Parse human feedback for specific modifications
        feedback = state.get("human_feedback", "")
        
        # Simple modification parsing (would be enhanced with NLP)
        modifications = []
        if "more agents" in feedback.lower():
            modifications.append({"type": "increase_agent_count", "details": "Add more agents"})
        if "fewer agents" in feedback.lower():
            modifications.append({"type": "decrease_agent_count", "details": "Reduce agent count"})
        if "different role" in feedback.lower():
            modifications.append({"type": "modify_roles", "details": "Change agent roles"})
        
        return modifications
    
    def _apply_modifications_to_plan(self, current_plan: List[Dict[str, Any]], modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply modifications to the current agent plan"""
        modified_plan = current_plan.copy()
        
        for mod in modifications:
            if mod["type"] == "increase_agent_count":
                # Add a generic helper agent
                modified_plan.append({
                    "agent_id": f"agent_{len(modified_plan)+1}_helper",
                    "role": "Helper",
                    "capabilities": ["general_assistance"],
                    "memory_access": "standard",
                    "reasoning": "Added based on human feedback"
                })
            elif mod["type"] == "decrease_agent_count" and len(modified_plan) > 1:
                # Remove the last agent
                modified_plan.pop()
        
        return modified_plan
    
    def _compare_plans(self, old_plan: List[Dict[str, Any]], new_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare two agent plans and return differences"""
        return {
            "old_agent_count": len(old_plan),
            "new_agent_count": len(new_plan),
            "agents_added": len(new_plan) - len(old_plan),
            "changes_summary": f"Plan modified from {len(old_plan)} to {len(new_plan)} agents"
        }
    
    # Finalization and Metrics
    
    def _finalize_configuration_with_tracking(self, state: OrchestrationState) -> Dict[str, Any]:
        """Finalize configuration with comprehensive tracking"""
        return {
            "final_agent_count": len(state.get("created_agents", [])),
            "memory_mode": state["user_preferences"].get("memory_mode", "shared"),
            "communication_mode": state["user_preferences"].get("communication_mode", "blackboard"),
            "approval_iterations": state.get("approval_iterations", 0),
            "configuration_timestamp": datetime.now().isoformat()
        }
    
    def _establish_baseline_metrics(self, state: OrchestrationState) -> Dict[str, Any]:
        """Establish baseline performance metrics"""
        return {
            "orchestration_start_time": datetime.now().isoformat(),
            "agent_count": len(state.get("created_agents", [])),
            "complexity_estimate": "medium",  # Would be calculated
            "expected_performance_indicators": ["task_completion_rate", "collaboration_efficiency", "output_quality"]
        }
    
    def _calculate_orchestration_effectiveness(self, state: OrchestrationState) -> Dict[str, Any]:
        """Calculate orchestration effectiveness metrics"""
        return {
            "approval_efficiency": 1.0 / max(state.get("approval_iterations", 1), 1),
            "error_rate": len(state.get("error_history", [])) / max(len(state.get("orchestration_decisions", [])), 1),
            "configuration_stability": 1.0 - (len(state.get("agent_modifications_history", [])) / 10.0)  # Normalized
        }
    
    def _store_human_interaction_pattern(self, config_summary: Dict[str, Any], human_response: Dict[str, Any]):
        """Store human interaction pattern for learning in memory"""
        try:
            pattern = {
                "configuration_type": config_summary,
                "human_response": human_response,
                "modification_requested": human_response.get("feedback", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            self.learning_patterns["human_feedback_patterns"].append(pattern)
            
            # Keep only last 50 interaction patterns to prevent memory bloat
            if len(self.learning_patterns["human_feedback_patterns"]) > 50:
                self.learning_patterns["human_feedback_patterns"] = self.learning_patterns["human_feedback_patterns"][-50:]
                
        except Exception as e:
            logger.error(f"Failed to store human interaction pattern: {e}")
    
    # Fallback Methods
    
    def _get_fallback_agent_plan(self, task_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get fallback agent plan using rule-based approach when LLM fails"""
        task_description = task_config.get("task_description", "")
        task_type = self._detect_task_type_fallback(task_description)
        
        logger.info(f"🔄 Using fallback planning for {task_type} task")
        
        # Simple fallback based on detected task type
        if task_type == "coding":
            return [
                {
                    "agent_id": "agent_1_developer",
                    "role": "Software Developer",
                    "capabilities": ["coding", "debugging", "testing"],
                    "memory_access": "standard",
                    "reasoning": "Fallback developer agent for coding tasks"
                },
                {
                    "agent_id": "agent_2_reviewer",
                    "role": "Code Reviewer",
                    "capabilities": ["code_review", "quality_assurance"],
                    "memory_access": "standard",
                    "reasoning": "Fallback reviewer agent for code quality"
                }
            ]
        elif task_type == "data_analysis":
            return [
                {
                    "agent_id": "agent_1_analyst",
                    "role": "Data Analyst",
                    "capabilities": ["data_analysis", "visualization"],
                    "memory_access": "standard", 
                    "reasoning": "Fallback analyst agent for data tasks"
                }
            ]
        else:
            # Generic fallback
            return [
                {
                    "agent_id": "agent_1_coordinator",
                    "role": "Task Coordinator",
                    "capabilities": ["coordination", "task_management"],
                    "memory_access": "standard",
                    "reasoning": "Fallback coordinator agent"
                },
                {
                    "agent_id": "agent_2_executor",
                    "role": "Task Executor", 
                    "capabilities": ["task_execution", "problem_solving"],
                    "memory_access": "standard",
                    "reasoning": "Fallback executor agent"
                }
            ]
    
    # Public Interface Methods
    
    def create_initial_state(self, task_config: Dict[str, Any], user_preferences: Dict[str, Any] = None) -> OrchestrationState:
        """Create initial orchestration state"""
        if user_preferences is None:
            user_preferences = {}
        
        return OrchestrationState(
            task_config=task_config,
            user_preferences=user_preferences,
            agent_plan=[],
            created_agents=[],
            agent_creation_reasoning=[],
            agent_modifications_history=[],
            memory_manager=None,
            communication_manager=None,
            human_feedback=None,
            human_feedback_history=[],
            needs_modifications=False,
            human_approved=False,
            approval_iterations=0,
            current_step="",
            execution_phase="",
            step_timestamps={},
            orchestration_decisions=[],
            agent_performance_metrics={},
            task_progress_milestones=[],
            orchestration_effectiveness={},
            error_message=None,
            error_history=[],
            recovery_attempts=0
        )
    
    def run_orchestration(self, task_config: Dict[str, Any], user_preferences: Dict[str, Any] = None, thread_id: str = None) -> OrchestrationState:
        """Run the complete orchestration workflow"""
        if not thread_id:
            thread_id = f"orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        initial_state = self.create_initial_state(task_config, user_preferences)
        
        try:
            # Run the workflow with state persistence
            config = {"configurable": {"thread_id": thread_id}}
            final_state = self.app.invoke(initial_state, config)
            
            logger.info(f"✅ Orchestration completed for thread {thread_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}")
            # Return state with error information
            initial_state["error_message"] = str(e)
            initial_state["error_history"].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "context": "orchestration_execution"
            })
            return initial_state
    
    def get_orchestration_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get orchestration history for a specific thread"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            history = []
            
            # Get state snapshots from checkpointer
            for checkpoint in self.memory.list(config):
                history.append({
                    "timestamp": checkpoint.ts,
                    "step": checkpoint.metadata.get("step", "unknown"),
                    "state_summary": {
                        "current_step": checkpoint.values.get("current_step", ""),
                        "execution_phase": checkpoint.values.get("execution_phase", ""),
                        "agent_count": len(checkpoint.values.get("created_agents", [])),
                        "approval_iterations": checkpoint.values.get("approval_iterations", 0)
                    }
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get orchestration history: {e}")
            return []
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights from in-memory stored patterns"""
        try:
            human_feedback_patterns = self.learning_patterns.get("human_feedback_patterns", [])
            
            return {
                "total_human_interactions": len(human_feedback_patterns),
                "learning_database_size": {
                    "human_interactions": len(human_feedback_patterns)
                },
                "in_memory_storage": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning insights: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    example_config = {
        "task_description": "Develop a web application for task management with user authentication and real-time collaboration features",
        "user_preferences": {
            "preferred_agent_count": 4,
            "memory_mode": "shared",
            "communication_mode": "blackboard"
        },
        "environment_config": {
            "available_tools": ["web_development", "database", "authentication"],
            "constraints": {"timeline": "2 weeks", "budget": "limited"},
            "success_criteria": "Functional web app with all specified features"
        }
    }
    
    # Initialize coordination engine
    engine = LangGraphCoordinationEngine()
    
    # Run orchestration
    result = engine.run_orchestration(
        task_config=example_config,
        user_preferences=example_config["user_preferences"]
    )
    
    print("\n🎯 Orchestration Results:")
    print(f"Final step: {result.get('current_step', 'unknown')}")
    print(f"Execution phase: {result.get('execution_phase', 'unknown')}")
    print(f"Agents created: {len(result.get('created_agents', []))}")
    print(f"Approval iterations: {result.get('approval_iterations', 0)}")
    print(f"Orchestration decisions: {len(result.get('orchestration_decisions', []))}")
    
    if result.get('error_message'):
        print(f"❌ Error: {result['error_message']}")
    else:
        print("✅ Orchestration completed successfully!")
    
    # Get learning insights
    insights = engine.get_learning_insights()
    print(f"\n📚 Learning Insights: {insights}")
