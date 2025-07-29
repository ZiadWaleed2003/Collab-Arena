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
    # Added recipient_id, making it optional for broadcast-style messages
    recipient_id: Optional[str] = None
    # Automatically generate a unique ID and timestamp when the object is created
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    # Default message type and metadata
    message_type: str = "response"  # e.g., "response", "question", "solution", "analysis"
    metadata: Dict[str, Any] = field(default_factory=dict)