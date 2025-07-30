from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

@dataclass
class Message:
    """Represents a message on the Blackboard"""
    id: str
    agent_id: str
    agent_role: str
    content: str
    timestamp: datetime
    message_type: str = "response"  # "response", "question", "solution", "analysis"
    metadata: Dict[str, Any] = field(default_factory=dict)