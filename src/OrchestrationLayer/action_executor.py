"""
LangGraph-based Action Executor with Agent-driven Intelligent Action Management

This module implements the complete action execution workflow using LangGraph with:
- Action Executor as an Agent instance with short-term memory
- Environment perception and state management
- Intelligent agent selection and communication
- Action evaluation and execution control
- Performance tracking and learning from execution patterns
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

# Import existing components
from src.agent import Agent
from src.MemoryModule.memory_manager import MemoryManager
from src.CommunicationModule.communication_manager import CommunicationManager, CommunicationMode, create_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionExecutionState(TypedDict):
    """Complete state schema for action execution tracking"""
    
    # Input from coordination engine
    task_config: Dict[str, Any]
    available_agents: List[Dict[str, Any]]  # Serializable agent configurations
    environment_config: Dict[str, Any]
    problem_statement: str
    
    # Execution tracking
    current_step: str
    execution_phase: str  # "perception", "selection", "communication", "evaluation", "execution"
    step_timestamps: Dict[str, str]
    
    # Environment state
    environment_state: Dict[str, Any]
    environment_changes: List[Dict[str, Any]]
    
    # Agent selection and communication
    selected_agent_id: Optional[str]
    agent_selection_reasoning: str
    agent_communication_history: List[Dict[str, Any]]
    
    # Action evaluation and execution
    proposed_action: Optional[Dict[str, Any]]
    action_evaluation: Dict[str, Any]
    execution_result: Optional[Dict[str, Any]]
    action_feedback: Optional[str]
    
    # Performance and learning
    execution_decisions: List[Dict[str, Any]]
    agent_performance_tracking: Dict[str, Any]
    execution_effectiveness: Dict[str, Any]
    
    # Error handling
    error_message: Optional[str]
    error_history: List[Dict[str, Any]]
    recovery_attempts: int
    
    # Final results
    execution_complete: bool
    final_result: Optional[Dict[str, Any]]


class ActionExecutor:
    """
    LangGraph-based Action Executor with Agent-driven execution intelligence
    """
    
    def __init__(self):
        self.memory = MemorySaver()  # In-memory storage for current session
        self.workflow = StateGraph(ActionExecutionState)
        self.app = None
        self.agents = []
        
        # Create Action Executor agent with short-term memory
        self.action_executor_agent = self._create_action_executor_agent()
        
        # Communication manager for agent interaction
        self.comm_manager = CommunicationManager(mode=CommunicationMode.DIRECT)
        
        # Learning patterns for execution improvement
        self.execution_patterns = {
            "agent_performance_history": [],
            "successful_action_patterns": [],
            "environment_change_patterns": []
        }
        
        self._setup_workflow()
    
    def _create_action_executor_agent(self) -> Agent:
        """Create the Action Executor agent with appropriate configuration"""
        
        action_executor_system_prompt = "".join([
            "You are an intelligent Action Executor Agent responsible for managing and executing actions in a multi-agent system.\n\n",
            "Your primary responsibilities:\n",
            "1. Environment Perception: Analyze current environment state and track changes\n",
            "2. Agent Selection: Intelligently select the most appropriate agent for current tasks\n",
            "3. Action Evaluation: Assess proposed actions for quality, safety, and effectiveness\n",
            "4. Execution Control: Manage action execution and handle feedback\n",
            "5. Performance Tracking: Learn from execution patterns and agent performance\n\n",
            "Key capabilities:\n",
            "- Environment state analysis and change detection\n",
            "- Agent capability matching with task requirements\n",
            "- Action quality assessment and risk evaluation\n",
            "- Execution coordination and feedback management\n",
            "- Performance analytics and learning pattern recognition\n\n",
            "Decision Framework:\n",
            "- Environment Analysis: Current state, constraints, available resources\n",
            "- Agent Matching: Capabilities, past performance, specialization fit\n",
            "- Action Assessment: Feasibility, safety, expected outcomes, resource requirements\n",
            "- Execution Strategy: Timing, monitoring, fallback plans\n\n",
            "Communication Style:\n",
            "- Be analytical and systematic in your reasoning\n",
            "- Provide clear rationale for agent selection decisions\n",
            "- Evaluate actions objectively with specific criteria\n",
            "- Track and learn from execution patterns\n",
            "- Adapt strategies based on performance data\n\n",
            "Memory Usage:\n",
            "- Store environment state changes for pattern recognition\n",
            "- Track agent performance across different task types\n",
            "- Remember successful action patterns for future reference\n",
            "- Learn from failures and adapt selection criteria\n\n",
            "Always provide structured analysis with clear reasoning and confidence scores.\n",
            "Be proactive in identifying potential issues and suggesting improvements.\n",
            "Focus on optimizing overall system performance through intelligent coordination."])


        # Create memory manager with short-term memory configuration
        memory_manager = MemoryManager(memory_type="short_term")
        
        # Create and return the Action Executor agent
        action_executor_agent = Agent(
            agent_id="action_executor",
            role="Action Executor",
            system_prompt=action_executor_system_prompt,
            memory_manager=memory_manager
        )
        
        logger.info("✅ Created Action Executor Agent with short-term memory")
        return action_executor_agent
    
    def _setup_workflow(self):
        """Setup the complete LangGraph workflow for action execution"""
        
        # Add all execution nodes
        self.workflow.add_node("environment_perception", self._environment_perception_node)
        self.workflow.add_node("agent_selection", self._agent_selection_node)
        self.workflow.add_node("agent_communication", self._agent_communication_node)
        self.workflow.add_node("action_evaluation", self._action_evaluation_node)
        self.workflow.add_node("execution_decision", self._execution_decision_node)
        self.workflow.add_node("environment_execution", self._environment_execution_node)
        self.workflow.add_node("feedback_processing", self._feedback_processing_node)
        self.workflow.add_node("completion_check", self._completion_check_node)
        
        # Define the workflow edges
        self.workflow.add_edge(START, "environment_perception")
        self.workflow.add_edge("environment_perception", "agent_selection")
        self.workflow.add_edge("agent_selection", "agent_communication")
        self.workflow.add_edge("agent_communication", "action_evaluation")
        self.workflow.add_edge("action_evaluation", "execution_decision")
        
        # Conditional routing from execution decision
        self.workflow.add_conditional_edges(
            "execution_decision",
            self._should_execute_action,
            {
                "execute": "environment_execution",
                "feedback": "feedback_processing",
                "reselect": "agent_selection"
            }
        )
        
        self.workflow.add_edge("environment_execution", "completion_check")
        self.workflow.add_edge("feedback_processing", "agent_communication")
        
        # Conditional routing from completion check
        self.workflow.add_conditional_edges(
            "completion_check",
            self._is_execution_complete,
            {
                "complete": END,
                "continue": "environment_perception"
            }
        )
        
        # Compile with checkpointing for persistence
        self.app = self.workflow.compile(checkpointer=self.memory)
        logger.info("✅ Action Execution workflow compiled successfully")
    
    # LangGraph Node Implementations
    
    def _environment_perception_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Environment Perception Node: Analyze current environment state
        TRACKS: environment changes, state analysis, perception patterns
        """
        logger.info("🌍 Environment Perception Node: Analyzing environment state")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "environment_perception"
        state["execution_phase"] = "perception"
        state["step_timestamps"]["environment_perception"] = current_time
        
        try:
            # Create environment perception prompt for Action Executor agent
            perception_prompt = self._create_environment_perception_prompt(state)
            
            # Use Action Executor agent to analyze environment
            perception_response = self.action_executor_agent.generate_response(
                problem=perception_prompt,
                recent_messages=[]
            )
            
            # Parse and store environment analysis
            environment_analysis = self._parse_environment_analysis(perception_response)
            state["environment_state"] = environment_analysis
            
            # Track environment changes
            if state.get("environment_changes"):
                # Compare with previous state to detect changes
                change_detected = self._detect_environment_changes(
                    state["environment_changes"][-1] if state["environment_changes"] else {},
                    environment_analysis
                )
                if change_detected:
                    state["environment_changes"].append({
                        "timestamp": current_time,
                        "change_type": "state_update",
                        "previous_state": state["environment_changes"][-1] if state["environment_changes"] else {},
                        "new_state": environment_analysis,
                        "detected_changes": change_detected
                    })
            else:
                state["environment_changes"] = [{
                    "timestamp": current_time,
                    "change_type": "initial_state",
                    "state": environment_analysis
                }]
            
            # Store perception event in Action Executor's short-term memory
            perception_event = {
                "type": "environment_perception",
                "content": f"Analyzed environment state: {environment_analysis.get('summary', 'Unknown')}",
                "state_complexity": environment_analysis.get("complexity", "medium"),
                "detected_changes": len(state["environment_changes"]),
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(perception_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "environment_perception",
                "decision_type": "environment_analysis",
                "analysis_result": environment_analysis,
                "changes_detected": len(state["environment_changes"]),
                "agent_response": perception_response
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Environment perception completed. State: {environment_analysis.get('summary', 'Analyzed')}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "environment_perception",
                "error": str(e),
                "recovery_action": "use_fallback_environment_state"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Fallback environment state
            state["environment_state"] = {
                "summary": "Fallback environment state",
                "complexity": "unknown",
                "available_resources": [],
                "constraints": []
            }
            logger.error(f"❌ Environment perception error: {e}. Using fallback state.")
        
        return state
    
    def _agent_selection_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Agent Selection Node: Intelligently select the most appropriate agent
        TRACKS: selection reasoning, agent matching, capability analysis
        """
        logger.info("🎯 Agent Selection Node: Selecting optimal agent for current task")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "agent_selection"
        state["execution_phase"] = "selection"
        state["step_timestamps"]["agent_selection"] = current_time
        
        try:
            # Create agent selection prompt for Action Executor agent
            selection_prompt = self._create_agent_selection_prompt(state)
            
            # Use Action Executor agent for intelligent selection
            selection_response = self.action_executor_agent.generate_response(
                problem=selection_prompt,
                recent_messages=[]
            )
            
            # Parse selection decision
            selection_result = self._parse_agent_selection(selection_response, state["available_agents"])
            
            state["selected_agent_id"] = selection_result.get("selected_agent_id")
            state["agent_selection_reasoning"] = selection_result.get("reasoning", "")
            
            # Store selection event in short-term memory
            selection_event = {
                "type": "agent_selection",
                "content": f"Selected agent: {state['selected_agent_id']}",
                "reasoning": state["agent_selection_reasoning"],
                "available_count": len(state["available_agents"]),
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(selection_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "agent_selection",
                "decision_type": "agent_selection",
                "selected_agent": state["selected_agent_id"],
                "selection_reasoning": state["agent_selection_reasoning"],
                "confidence_score": selection_result.get("confidence", 0.8),
                "agent_response": selection_response
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Agent selection completed. Selected: {state['selected_agent_id']}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "agent_selection",
                "error": str(e),
                "recovery_action": "select_fallback_agent"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Fallback: select first available agent
            if state["available_agents"]:
                state["selected_agent_id"] = state["available_agents"][0].get("agent_id", "unknown")
                state["agent_selection_reasoning"] = f"Fallback selection due to error: {str(e)}"
            
            logger.error(f"❌ Agent selection error: {e}. Using fallback selection.")
        
        return state
    
    def _agent_communication_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Agent Communication Node: Communicate with selected agent for action recommendation
        TRACKS: communication history, agent responses, context sharing
        """
        logger.info("💬 Agent Communication Node: Communicating with selected agent")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "agent_communication"
        state["execution_phase"] = "communication"
        state["step_timestamps"]["agent_communication"] = current_time
        
        try:
            # Create communication prompt for the selected agent
            communication_prompt = self._create_agent_communication_prompt(state)
            
            # Use Action Executor agent to formulate the communication
            communication_strategy = self.action_executor_agent.generate_response(
                problem=f"Formulate communication strategy for agent {state['selected_agent_id']}: {communication_prompt}",
                recent_messages=[]
            )
            
            # Simulate agent communication (in real implementation, this would be actual agent interaction)
            agent_response = self._simulate_agent_communication(
                state["selected_agent_id"],
                communication_prompt,
                state
            )
            
            # Store communication history
            communication_record = {
                "timestamp": current_time,
                "agent_id": state["selected_agent_id"],
                "prompt_sent": communication_prompt,
                "agent_response": agent_response,
                "communication_strategy": communication_strategy
            }
            
            if "agent_communication_history" not in state:
                state["agent_communication_history"] = []
            state["agent_communication_history"].append(communication_record)
            
            # Extract proposed action from agent response
            proposed_action = self._extract_proposed_action(agent_response)
            state["proposed_action"] = proposed_action
            
            # Store communication event in short-term memory
            communication_event = {
                "type": "agent_communication",
                "content": f"Communicated with {state['selected_agent_id']}",
                "response_received": bool(agent_response),
                "action_proposed": bool(proposed_action),
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(communication_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "agent_communication",
                "decision_type": "agent_communication",
                "agent_id": state["selected_agent_id"],
                "communication_success": bool(agent_response),
                "proposed_action": proposed_action,
                "response_quality": self._assess_response_quality(agent_response)
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Agent communication completed. Action proposed: {bool(proposed_action)}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "agent_communication",
                "error": str(e),
                "recovery_action": "generate_fallback_action"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Fallback: generate a basic action
            state["proposed_action"] = {
                "action_type": "fallback",
                "description": "Basic action due to communication failure",
                "parameters": {},
                "confidence": 0.3
            }
            
            logger.error(f"❌ Agent communication error: {e}. Using fallback action.")
        
        return state
    
    def _action_evaluation_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Action Evaluation Node: Evaluate proposed action for quality and safety
        TRACKS: evaluation criteria, quality assessment, decision reasoning
        """
        logger.info("⚖️ Action Evaluation Node: Evaluating proposed action")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "action_evaluation"
        state["execution_phase"] = "evaluation"
        state["step_timestamps"]["action_evaluation"] = current_time
        
        try:
            # Create evaluation prompt for Action Executor agent
            evaluation_prompt = self._create_action_evaluation_prompt(state)
            
            # Use Action Executor agent for intelligent evaluation
            evaluation_response = self.action_executor_agent.generate_response(
                problem=evaluation_prompt,
                recent_messages=[]
            )
            
            # Parse evaluation results
            evaluation_result = self._parse_action_evaluation(evaluation_response)
            state["action_evaluation"] = evaluation_result
            
            # Store evaluation event in short-term memory
            evaluation_event = {
                "type": "action_evaluation",
                "content": f"Evaluated action: {evaluation_result.get('decision', 'unknown')}",
                "quality_score": evaluation_result.get("quality_score", 0.5),
                "safety_score": evaluation_result.get("safety_score", 0.5),
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(evaluation_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "action_evaluation",
                "decision_type": "action_evaluation",
                "evaluation_result": evaluation_result,
                "quality_score": evaluation_result.get("quality_score", 0.5),
                "safety_score": evaluation_result.get("safety_score", 0.5),
                "overall_decision": evaluation_result.get("decision", "unknown"),
                "agent_response": evaluation_response
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Action evaluation completed. Decision: {evaluation_result.get('decision', 'unknown')}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "action_evaluation",
                "error": str(e),
                "recovery_action": "conservative_evaluation"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Conservative fallback evaluation
            state["action_evaluation"] = {
                "decision": "needs_improvement",
                "quality_score": 0.4,
                "safety_score": 0.6,
                "reasoning": f"Conservative evaluation due to error: {str(e)}"
            }
            
            logger.error(f"❌ Action evaluation error: {e}. Using conservative evaluation.")
        
        return state
    
    def _execution_decision_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Execution Decision Node: Decide whether to execute, provide feedback, or reselect
        TRACKS: decision logic, routing decisions, condition evaluation
        """
        logger.info("🔀 Execution Decision Node: Making execution decision")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "execution_decision"
        state["step_timestamps"]["execution_decision"] = current_time
        
        try:
            evaluation = state.get("action_evaluation", {})
            decision = evaluation.get("decision", "needs_improvement")
            quality_score = evaluation.get("quality_score", 0.5)
            safety_score = evaluation.get("safety_score", 0.5)
            
            # Store decision event in short-term memory
            decision_event = {
                "type": "execution_decision",
                "content": f"Decision: {decision}",
                "quality_score": quality_score,
                "safety_score": safety_score,
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(decision_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "execution_decision",
                "decision_type": "routing_decision",
                "routing_choice": decision,
                "quality_score": quality_score,
                "safety_score": safety_score,
                "reasoning": evaluation.get("reasoning", "")
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Execution decision completed. Route: {decision}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "execution_decision",
                "error": str(e),
                "recovery_action": "default_to_feedback"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Default to feedback if error occurs
            state["action_evaluation"] = {
                "decision": "needs_improvement",
                "reasoning": f"Default to feedback due to error: {str(e)}"
            }
            
            logger.error(f"❌ Execution decision error: {e}. Defaulting to feedback.")
        
        return state
    
    def _environment_execution_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Environment Execution Node: Execute the approved action
        TRACKS: execution results, environment changes, performance metrics
        """
        logger.info("🚀 Environment Execution Node: Executing approved action")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "environment_execution"
        state["execution_phase"] = "execution"
        state["step_timestamps"]["environment_execution"] = current_time
        
        try:
            # Simulate action execution (in real implementation, this would interface with actual environment)
            execution_result = self._simulate_action_execution(state["proposed_action"], state)
            state["execution_result"] = execution_result
            
            # Update environment state based on execution
            if execution_result.get("success"):
                updated_state = self._update_environment_state(
                    state["environment_state"],
                    execution_result
                )
                state["environment_state"] = updated_state
                
                # Track environment change
                state["environment_changes"].append({
                    "timestamp": current_time,
                    "change_type": "action_execution",
                    "action": state["proposed_action"],
                    "result": execution_result,
                    "new_state": updated_state
                })
            
            # Store execution event in short-term memory
            execution_event = {
                "type": "environment_execution",
                "content": f"Executed action: {state['proposed_action'].get('description', 'Unknown')}",
                "success": execution_result.get("success", False),
                "impact": execution_result.get("impact", "unknown"),
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(execution_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "environment_execution",
                "decision_type": "action_execution",
                "action_executed": state["proposed_action"],
                "execution_result": execution_result,
                "success": execution_result.get("success", False),
                "impact_level": execution_result.get("impact", "unknown")
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Action execution completed. Success: {execution_result.get('success', False)}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "environment_execution",
                "error": str(e),
                "recovery_action": "record_execution_failure"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Record failed execution
            state["execution_result"] = {
                "success": False,
                "error": str(e),
                "impact": "none",
                "message": "Execution failed due to error"
            }
            
            logger.error(f"❌ Action execution error: {e}")
        
        return state
    
    def _feedback_processing_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Feedback Processing Node: Process feedback for action improvement
        TRACKS: feedback content, improvement suggestions, learning patterns
        """
        logger.info("📝 Feedback Processing Node: Processing action feedback")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "feedback_processing"
        state["step_timestamps"]["feedback_processing"] = current_time
        
        try:
            # Create feedback prompt for Action Executor agent
            feedback_prompt = self._create_feedback_prompt(state)
            
            # Use Action Executor agent to generate feedback
            feedback_response = self.action_executor_agent.generate_response(
                problem=feedback_prompt,
                recent_messages=[]
            )
            
            state["action_feedback"] = feedback_response
            
            # Store feedback event in short-term memory
            feedback_event = {
                "type": "feedback_processing",
                "content": f"Generated feedback for improvement",
                "feedback_length": len(feedback_response) if feedback_response else 0,
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(feedback_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "feedback_processing",
                "decision_type": "feedback_generation",
                "feedback_content": feedback_response,
                "improvement_suggestions": self._extract_improvement_suggestions(feedback_response)
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info("✅ Feedback processing completed")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "feedback_processing",
                "error": str(e),
                "recovery_action": "generate_generic_feedback"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Generate generic feedback
            state["action_feedback"] = "Please improve the action quality and safety before resubmission."
            
            logger.error(f"❌ Feedback processing error: {e}. Using generic feedback.")
        
        return state
    
    def _completion_check_node(self, state: ActionExecutionState) -> ActionExecutionState:
        """
        Completion Check Node: Determine if execution is complete or should continue
        TRACKS: completion criteria, success metrics, continuation decisions
        """
        logger.info("🏁 Completion Check Node: Checking execution completion")
        
        current_time = datetime.now().isoformat()
        state["current_step"] = "completion_check"
        state["step_timestamps"]["completion_check"] = current_time
        
        try:
            # Create completion check prompt for Action Executor agent
            completion_prompt = self._create_completion_check_prompt(state)
            
            # Use Action Executor agent to assess completion
            completion_response = self.action_executor_agent.generate_response(
                problem=completion_prompt,
                recent_messages=[]
            )
            
            # Parse completion decision
            completion_result = self._parse_completion_decision(completion_response)
            state["execution_complete"] = completion_result.get("complete", False)
            
            if state["execution_complete"]:
                # Generate final result summary
                final_result = self._generate_final_result(state)
                state["final_result"] = final_result
            
            # Store completion event in short-term memory
            completion_event = {
                "type": "completion_check",
                "content": f"Execution complete: {state['execution_complete']}",
                "completion_reasoning": completion_result.get("reasoning", ""),
                "timestamp": current_time
            }
            self.action_executor_agent.add_to_short_term_memory(completion_event)
            
            # Record execution decision
            execution_decision = {
                "timestamp": current_time,
                "node": "completion_check",
                "decision_type": "completion_assessment",
                "execution_complete": state["execution_complete"],
                "completion_reasoning": completion_result.get("reasoning", ""),
                "agent_response": completion_response
            }
            state["execution_decisions"].append(execution_decision)
            
            logger.info(f"✅ Completion check completed. Complete: {state['execution_complete']}")
            
        except Exception as e:
            error_info = {
                "timestamp": current_time,
                "node": "completion_check",
                "error": str(e),
                "recovery_action": "assume_completion"
            }
            state["error_history"].append(error_info)
            state["error_message"] = str(e)
            state["recovery_attempts"] += 1
            
            # Conservative approach: assume completion on error
            state["execution_complete"] = True
            state["final_result"] = {
                "status": "completed_with_errors",
                "message": f"Execution assumed complete due to error: {str(e)}"
            }
            
            logger.error(f"❌ Completion check error: {e}. Assuming completion.")
        
        return state
    
    # Routing Functions
    
    def _should_execute_action(self, state: ActionExecutionState) -> str:
        """Determine routing based on action evaluation"""
        evaluation = state.get("action_evaluation", {})
        decision = evaluation.get("decision", "needs_improvement")
        
        if decision == "approved" or decision == "execute":
            return "execute"
        elif decision == "reselect_agent":
            return "reselect"
        else:
            return "feedback"
    
    def _is_execution_complete(self, state: ActionExecutionState) -> str:
        """Determine if execution workflow should complete or continue"""
        if state.get("execution_complete", False):
            return "complete"
        return "continue"
    
    # Helper Methods for Prompt Creation
    
    def _create_environment_perception_prompt(self, state: ActionExecutionState) -> str:
        """Create prompt for environment perception analysis"""
        task_description = state["task_config"].get("task_description", "")
        environment_config = state.get("environment_config", {})
        
        prompt = "".join([
                    "ENVIRONMENT PERCEPTION ANALYSIS\n\n",
                    f"Task Description: {task_description}\n\n",
                    "Environment Configuration:\n",
                    f"{json.dumps(environment_config, indent=2)}\n\n",
                    f"Problem Statement: {state.get('problem_statement', '')}\n\n",
                    f"Previous Environment Changes: {len(state.get('environment_changes', []))} recorded\n\n",
                    "Please analyze the current environment state and provide:\n\n",
                    "1. Environment Summary: Current state overview\n",
                    "2. Available Resources: What resources are currently available\n",
                    "3. Constraints: Current limitations and restrictions\n",
                    "4. Complexity Assessment: Low/Medium/High complexity level\n",
                    "5. Change Detection: Any significant changes from previous states\n",
                    "6. Risk Factors: Potential risks or challenges\n\n",
                    "Provide your analysis in JSON format:\n",
                    '{"summary": "brief overview", '
                    '"complexity": "low/medium/high", '
                    '"available_resources": [], '
                    '"constraints": [], '
                    '"risks": [], '
                    '"change_assessment": ""}\n\n',
                    "Be thorough and analytical in your assessment."
                ])
        
        return prompt

    
    def _create_agent_selection_prompt(self, state: ActionExecutionState) -> str:
        """Create prompt for intelligent agent selection"""
        environment_state = state.get("environment_state", {})
        available_agents = state["available_agents"]
        
        agents_info = "\n".join([
            f"Agent {i+1}: {agent.get('agent_id', 'unknown')} - {agent.get('role', 'Unknown Role')}\n"
            f"  Capabilities: {agent.get('capabilities', [])}\n"
            f"  Memory Access: {agent.get('memory_access', 'standard')}"
            for i, agent in enumerate(available_agents)
        ])
        
        prompt = "".join([
            "INTELLIGENT AGENT SELECTION\n\n",
            "Current Environment State:\n",
            f"{json.dumps(environment_state, indent=2)}\n\n",
            "Available Agents:\n",
            f"{agents_info}\n\n",
            f"Task Requirements: {state.get('problem_statement', '')}\n\n",
            "Please select the most appropriate agent based on:\n\n",
            "1. Capability Matching: How well agent capabilities match current needs\n",
            "2. Environment Fit: Agent's suitability for current environment\n",
            "3. Past Performance: Consider any historical performance data\n",
            "4. Task Complexity: Agent's ability to handle current complexity level\n",
            "5. Resource Requirements: Agent's resource needs vs. availability\n\n",
            "Provide your selection in JSON format:\n",
            '{"selected_agent_id": "agent_id", '
            '"reasoning": "detailed reasoning", '
            '"confidence": 0.0-1.0, '
            '"alternative_options": []}\n\n',
            "Be specific about why this agent is the best choice."])
        
        return prompt

    
    def _create_agent_communication_prompt(self, state: ActionExecutionState) -> str:
        """Create prompt for agent communication"""
        environment_state = state.get("environment_state", {})
        
        prompt = "".join([
                f"ACTION REQUEST FOR AGENT {state['selected_agent_id']}\n\n",
                "Environment Context:\n",
                f"{json.dumps(environment_state, indent=2)}\n\n",
                f"Task: {state.get('problem_statement', '')}\n\n",
                "Current Situation:\n",
                f"- Environment Complexity: {environment_state.get('complexity', 'medium')}\n",
                f"- Available Resources: {environment_state.get('available_resources', [])}\n",
                f"- Constraints: {environment_state.get('constraints', [])}\n\n",
                "Please provide a specific action recommendation that:\n",
                "1. Addresses the current task requirements\n",
                "2. Considers environmental constraints and resources\n",
                "3. Is feasible and safe to execute\n",
                "4. Provides clear expected outcomes\n\n",
                "Include action parameters, expected results, and any prerequisites."])
        
        return prompt

    
    def _create_action_evaluation_prompt(self, state: ActionExecutionState) -> str:
        """Create prompt for action evaluation"""
        proposed_action = state.get("proposed_action", {})
        environment_state = state.get("environment_state", {})
        prompt = "".join([
                        "ACTION EVALUATION AND ASSESSMENT\n",
                        "Proposed Action:\n",
                        f"{json.dumps(proposed_action, indent=2)}\n",
                        "Current Environment:\n",
                        f"{json.dumps(environment_state, indent=2)}\n",
                        f"Agent Source: {state.get('selected_agent_id', 'unknown')}\n",
                        "\n",
                        "Please evaluate this action on the following criteria:\n",
                        "1. Quality Assessment (0.0-1.0):\n",
                        "- Clarity and specificity of action\n",
                        "- Alignment with task requirements\n",
                        "- Completeness of parameters\n",
                        "\n",
                        "2. Safety Assessment (0.0-1.0):\n",
                        "- Risk level of execution\n",
                        "- Safety measures included\n",
                        "- Potential negative consequences\n",
                        "\n",
                        "3. Feasibility Assessment (0.0-1.0):\n",
                        "- Resource availability\n",
                        "- Technical feasibility\n",
                        "- Time requirements\n",
                        "\n",
                        "4. Expected Effectiveness (0.0-1.0):\n",
                        "- Likelihood of success\n",
                        "- Progress toward goal\n",
                        "- Expected outcome quality\n",
                        "\n",
                        "Based on your evaluation, make a decision:\n",
                        '- "approved": Action is ready for execution\n',
                        '- "needs_improvement": Action needs refinement\n',
                        '- "reselect_agent": Different agent should be selected\n',
                        "\n",
                        "Provide evaluation in JSON format:\n",
                        '{"decision": "approved/needs_improvement/reselect_agent", '
                        '"quality_score": 0.0, '
                        '"safety_score": 0.0, '
                        '"feasibility_score": 0.0, '
                        '"effectiveness_score": 0.0, '
                        '"reasoning": "detailed explanation", '
                        '"improvement_suggestions": []}'
                    ])
        
        return prompt
                        
    def _create_feedback_prompt(self, state: ActionExecutionState) -> str:
        """Create prompt for feedback generation"""
        proposed_action = state.get("proposed_action", {})
        evaluation = state.get("action_evaluation", {})
        
        prompt = "".join([
            "FEEDBACK GENERATION FOR ACTION IMPROVEMENT\n\n",
            "Proposed Action:\n",
            f"{json.dumps(proposed_action, indent=2)}\n\n",
            "Evaluation Results:\n",
            f"{json.dumps(evaluation, indent=2)}\n\n",
            f"Agent: {state.get('selected_agent_id', 'unknown')}\n\n",
            "Please provide constructive feedback to help the agent improve their action proposal:\n\n",
            "1. Specific Issues: What exactly needs improvement\n",
            "2. Improvement Suggestions: Concrete recommendations\n",
            "3. Quality Guidelines: Standards the action should meet\n",
            "4. Safety Considerations: Safety improvements needed\n",
            "5. Resource Optimization: Better resource utilization\n\n",
            "Make your feedback:\n",
            "- Specific and actionable\n",
            "- Constructive and helpful\n",
            "- Clear about expectations\n",
            "- Focused on improvement areas identified in evaluation\n\n",
            "Provide clear guidance on how to address the identified issues."
        ])

        return prompt

    def _create_completion_check_prompt(self, state: ActionExecutionState) -> str:
        """Create prompt for completion assessment"""
        execution_result = state.get("execution_result", {})
        task_config = state["task_config"]
        
        prompt = "".join([
        "EXECUTION COMPLETION ASSESSMENT\n\n",
        "Task Configuration:\n",
        f"{json.dumps(task_config, indent=2)}\n\n",
        "Execution Result:\n",
        f"{json.dumps(execution_result, indent=2)}\n\n",
        f"Execution History: {len(state.get('execution_decisions', []))} decisions made\n\n",
        f"Problem Statement: {state.get('problem_statement', '')}\n\n",
        "Please assess whether the execution is complete:\n\n",
        "1. Task Completion: Has the main task been accomplished?\n",
        "2. Success Criteria: Have success criteria been met?\n",
        "3. Quality Standards: Does the result meet quality expectations?\n",
        "4. Further Actions: Are additional actions needed?\n",
        "5. Error Handling: Have any errors been properly addressed?\n\n",
        "Consider:\n",
        "- Original task requirements\n",
        "- Execution success/failure\n",
        "- Quality of results\n",
        "- Need for additional iterations\n\n",
        "Provide assessment in JSON format:\n",
        '{"complete": true/false, '
        '"reasoning": "detailed explanation", '
        '"completion_percentage": 0.0-1.0, '
        '"recommendations": []}'
    ])
        
        return prompt
    
    # Helper Methods for Response Parsing
    
    def _parse_environment_analysis(self, response: str) -> Dict[str, Any]:
        """Parse environment analysis from Action Executor agent response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback parsing
        return {
            "summary": "Environment analyzed",
            "complexity": "medium",
            "available_resources": [],
            "constraints": [],
            "risks": [],
            "change_assessment": "No significant changes detected"
        }
    
    def _parse_agent_selection(self, response: str, available_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse agent selection from Action Executor agent response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Validate selected agent exists
                if result.get("selected_agent_id") in [agent.get("agent_id") for agent in available_agents]:
                    return result
        except:
            pass
        
        # Fallback: select first available agent
        if available_agents:
            return {
                "selected_agent_id": available_agents[0].get("agent_id", "unknown"),
                "reasoning": "Fallback selection - first available agent",
                "confidence": 0.5
            }
        
        return {
            "selected_agent_id": "unknown",
            "reasoning": "No agents available",
            "confidence": 0.0
        }
    
    def _parse_action_evaluation(self, response: str) -> Dict[str, Any]:
        """Parse action evaluation from Action Executor agent response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback evaluation
        return {
            "decision": "needs_improvement",
            "quality_score": 0.5,
            "safety_score": 0.5,
            "feasibility_score": 0.5,
            "effectiveness_score": 0.5,
            "reasoning": "Fallback evaluation - requires improvement",
            "improvement_suggestions": ["Please provide more detailed action parameters"]
        }
    
    def _parse_completion_decision(self, response: str) -> Dict[str, Any]:
        """Parse completion decision from Action Executor agent response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback completion decision
        return {
            "complete": True,
            "reasoning": "Fallback completion assessment",
            "completion_percentage": 0.8,
            "recommendations": []
        }
    
    # Simulation Methods (would be replaced with actual implementations)
    
    def _simulate_agent_communication(self, agent_id: str, prompt: str, state: ActionExecutionState) -> str:
        """Simulate agent communication (would be actual agent interaction in real implementation)"""
        # This would be replaced with actual agent communication
        return f"Agent {agent_id} proposes: Execute analysis task with parameters based on current environment state."
    
    def _extract_proposed_action(self, agent_response: str) -> Dict[str, Any]:
        """Extract proposed action from agent response"""
        # Simple extraction - would be more sophisticated in real implementation
        return {
            "action_type": "analysis",
            "description": agent_response[:100] if agent_response else "No action proposed",
            "parameters": {},
            "confidence": 0.7
        }
    
    def _simulate_action_execution(self, action: Dict[str, Any], state: ActionExecutionState) -> Dict[str, Any]:
        """Simulate action execution (would interface with actual environment)"""
        # Simulate execution result
        return {
            "success": True,
            "impact": "moderate",
            "message": f"Successfully executed {action.get('action_type', 'unknown')} action",
            "execution_time": 1.5,
            "resource_usage": {"cpu": 0.3, "memory": 0.2}
        }
    
    def _detect_environment_changes(self, previous_state: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect changes between environment states"""
        # Simple change detection
        changes = {}
        if previous_state.get("complexity") != current_state.get("complexity"):
            changes["complexity_change"] = {
                "from": previous_state.get("complexity"),
                "to": current_state.get("complexity")
            }
        
        return changes
    
    def _update_environment_state(self, current_state: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update environment state based on execution result"""
        updated_state = current_state.copy()
        
        # Update based on execution impact
        if execution_result.get("impact") == "high":
            updated_state["complexity"] = "high"
        elif execution_result.get("impact") == "low":
            updated_state["complexity"] = "low"
        
        updated_state["last_action"] = execution_result.get("message", "Unknown action")
        updated_state["last_update"] = datetime.now().isoformat()
        
        return updated_state
    
    def _assess_response_quality(self, response: str) -> Dict[str, Any]:
        """Assess quality of agent response"""
        if not response:
            return {"quality": "poor", "score": 0.2, "issues": ["No response provided"]}
        
        return {
            "quality": "good" if len(response) > 50 else "fair",
            "score": min(len(response) / 100, 1.0),
            "issues": [] if len(response) > 20 else ["Response too short"]
        }
    
    def _extract_improvement_suggestions(self, feedback: str) -> List[str]:
        """Extract improvement suggestions from feedback"""
        # Simple extraction - would be more sophisticated
        suggestions = []
        if "improve" in feedback.lower():
            suggestions.append("General improvement needed")
        if "specific" in feedback.lower():
            suggestions.append("Be more specific")
        if "safety" in feedback.lower():
            suggestions.append("Address safety concerns")
        
        return suggestions if suggestions else ["Review and refine action proposal"]
    
    def _generate_final_result(self, state: ActionExecutionState) -> Dict[str, Any]:
        """Generate final execution result summary"""
        execution_result = state.get("execution_result", {})
        
        return {
            "execution_success": execution_result.get("success", False),
            "final_state": state.get("environment_state", {}),
            "total_decisions": len(state.get("execution_decisions", [])),
            "agent_used": state.get("selected_agent_id", "unknown"),
            "execution_time": self._calculate_total_execution_time(state),
            "completion_timestamp": datetime.now().isoformat(),
            "summary": execution_result.get("message", "Execution completed")
        }
    
    def _calculate_total_execution_time(self, state: ActionExecutionState) -> float:
        """Calculate total execution time from timestamps"""
        timestamps = state.get("step_timestamps", {})
        if len(timestamps) < 2:
            return 0.0
        
        start_time = min(timestamps.values())
        end_time = max(timestamps.values())
        
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            return (end_dt - start_dt).total_seconds()
        except:
            return 0.0
    
    # Public Interface Methods
    
    def create_initial_state(self, task_config: Dict[str, Any], agents: List[Agent], 
                           problem_statement: str, environment_config: Dict[str, Any] = None) -> ActionExecutionState:
        """Create initial action execution state"""
        
        # Convert Agent instances to serializable configurations
        agent_configs = []
        for agent in self.agents:
            agent_config = {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "capabilities": getattr(agent, 'capabilities', []),
                "memory_access": "standard",  # Default value
                "system_prompt": agent.system_prompt
            }
            agent_configs.append(agent_config)
        
        return ActionExecutionState(
            task_config=task_config,
            available_agents=agent_configs,
            environment_config=environment_config or {},
            problem_statement=problem_statement,
            current_step="",
            execution_phase="",
            step_timestamps={},
            environment_state={},
            environment_changes=[],
            selected_agent_id=None,
            agent_selection_reasoning="",
            agent_communication_history=[],
            proposed_action=None,
            action_evaluation={},
            execution_result=None,
            action_feedback=None,
            execution_decisions=[],
            agent_performance_tracking={},
            execution_effectiveness={},
            error_message=None,
            error_history=[],
            recovery_attempts=0,
            execution_complete=False,
            final_result=None
        )
    
    def execute_with_agents(self, agents: List[Agent], task_config: Dict[str, Any], 
                          problem_statement: str, environment_config: Dict[str, Any] = None,
                          thread_id: str = None) -> ActionExecutionState:
        """Execute action workflow with provided agents"""
        
        if not thread_id:
            thread_id = f"action_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


        if not agents :
            logger.error("❌ agents were empty error Coordination engine probably passed it empty")

        self.agents = agents
        
        # Create initial state
        initial_state = self.create_initial_state(
            task_config=task_config,
            agents=agents,
            problem_statement=problem_statement,
            environment_config=environment_config
        )
        
        try:
            # Run the workflow with state persistence
            config = {"configurable": {"thread_id": thread_id}}
            final_state = self.app.invoke(initial_state, config)
            
            logger.info(f"✅ Action execution completed for thread {thread_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"❌ Action execution failed: {e}")
            # Return state with error information
            initial_state["error_message"] = str(e)
            initial_state["error_history"].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "context": "action_execution"
            })
            return initial_state
    
    def get_execution_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get action execution history for a specific thread"""
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
                        "selected_agent": checkpoint.values.get("selected_agent_id", ""),
                        "execution_complete": checkpoint.values.get("execution_complete", False)
                    }
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []
    
    def get_agent_performance_insights(self) -> Dict[str, Any]:
        """Get insights about agent performance from execution patterns"""
        try:
            performance_history = self.execution_patterns.get("agent_performance_history", [])
            
            return {
                "total_executions": len(performance_history),
                "execution_patterns": {
                    "agent_performance": len(performance_history),
                    "successful_actions": len(self.execution_patterns.get("successful_action_patterns", [])),
                    "environment_changes": len(self.execution_patterns.get("environment_change_patterns", []))
                },
                "action_executor_memory_usage": self.action_executor_agent.get_short_term_memory_info(),
                "learning_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance insights: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    # Example: Create Action Executor and simulate execution
    action_executor = ActionExecutor()
    
    # Example agents (would come from Coordination Engine)
    example_agents = [
        Agent(
            agent_id="problem_analyst",
            role="Problem Analyst",
            system_prompt="You are a problem analysis specialist.",
            memory_manager=MemoryManager(memory_type="shared")
        ),
        Agent(
            agent_id="solution_implementer", 
            role="Solution Implementer",
            system_prompt="You are a solution implementation specialist.",
            memory_manager=MemoryManager(memory_type="shared")
        )
    ]
    
    # Example task configuration
    example_task_config = {
        "task_description": "Analyze and solve a complex mathematical problem",
        "success_criteria": "Provide accurate solution with detailed explanation",
        "constraints": {"time_limit": "30 minutes", "resources": "standard"}
    }
    
    # Example problem statement
    example_problem = "Find the optimal solution for a system of linear equations with 3 variables"
    
    # Example environment configuration
    example_environment = {
        "available_tools": ["calculator", "graphing", "analysis"],
        "resource_limits": {"memory": "4GB", "time": "30min"},
        "safety_constraints": ["no_external_access", "read_only_files"]
    }
    
    print("🚀 Starting Action Execution Example...")
    
    # Execute with agents
    result = action_executor.execute_with_agents(
        agents=example_agents,
        task_config=example_task_config,
        problem_statement=example_problem,
        environment_config=example_environment
    )
    
    print("\n🎯 Action Execution Results:")
    print(f"Final step: {result.get('current_step', 'unknown')}")
    print(f"Execution phase: {result.get('execution_phase', 'unknown')}")
    print(f"Selected agent: {result.get('selected_agent_id', 'none')}")
    print(f"Execution complete: {result.get('execution_complete', False)}")
    print(f"Total decisions: {len(result.get('execution_decisions', []))}")
    print(f"Environment changes: {len(result.get('environment_changes', []))}")
    
    if result.get('error_message'):
        print(f"❌ Error: {result['error_message']}")
    else:
        print("✅ Action execution completed successfully!")
        
        if result.get('final_result'):
            final_result = result['final_result']
            print(f"\n📊 Final Result:")
            print(f"Success: {final_result.get('execution_success', False)}")
            print(f"Total time: {final_result.get('execution_time', 0):.2f}s")
            print(f"Summary: {final_result.get('summary', 'No summary')}")
    
    # Get performance insights
    insights = action_executor.get_agent_performance_insights()
    print(f"\n📈 Performance Insights: {insights}")
    
    # Get Action Executor agent's memory state
    memory_info = action_executor.action_executor_agent.get_short_term_memory_info()
    print(f"\n🧠 Action Executor Memory: {memory_info}")
