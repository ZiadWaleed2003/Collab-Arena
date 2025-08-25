from typing import Optional
import uuid
from dataclasses import dataclass, field
import datetime

from .event_type import EventType

@dataclass
class AuditEvent:
    "a data class to create any event when logging it"

    event_id : str = field(default_factory=lambda: str(uuid.uuid4()))
    time_stamp : datetime = field(default_factory= lambda: datetime.now().strftime('%Y%m%d_%H%M%S'))
    source : str 
    event_type : Optional[EventType]
    details : dict
