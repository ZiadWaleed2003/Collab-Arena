from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal

# Define the expected structure of the LLM's JSON output using Pydantic models

class TaskAnalysis(BaseModel):
    task_type: str = Field(..., description="The classified type of the task, e.g., 'coding', 'data_analysis'.")
    complexity_level: Literal['low', 'medium', 'high'] = Field(..., description="The assessed complexity of the task.")
    key_requirements: List[str] = Field(..., description="A list of key requirements extracted from the task.")
    reasoning: str = Field(..., description="Detailed reasoning for the analysis and classification.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the analysis.")

class AgentPlanItem(BaseModel):
    agent_id: str = Field(..., description="A unique identifier for the agent.")
    role: str = Field(..., description="The specific, creative role assigned to the agent.")
    capabilities: List[str] = Field(..., description="A list of capabilities this agent should have.")
    reasoning: str = Field(..., description="Explanation of why this agent is necessary for the team.")
    priority: Literal['low', 'medium', 'high'] = Field(..., description="The priority of this agent in the team.")

class RecommendedConfig(BaseModel):
    memory_mode: Literal['shared', 'isolated', 'rbac'] = Field(..., description="Recommended memory mode for the agent team.")
    communication_mode: Literal['direct', 'blackboard', 'pubsub'] = Field(..., description="Recommended communication protocol.")
    reasoning: str = Field(..., description="Justification for the recommended configuration.")

class OrchestratorResponse(BaseModel):
    """The complete, validated response from the orchestrator LLM."""
    task_analysis: TaskAnalysis
    agent_plan: List[AgentPlanItem]
    recommended_config: RecommendedConfig