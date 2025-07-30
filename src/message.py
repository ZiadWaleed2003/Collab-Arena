import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class Message:
    """Represents a message on the Blackboard"""
    agent_id: str
    agent_role: str
    content: str
    recipient_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_type: str = "response"  # e.g., "response", "question", "solution", "analysis"
    metadata: Dict[str, Any] = field(default_factory=dict)