from enum import Enum

class EventType(Enum):

    SYSTEM_START = 1
    AGENT_THINK  = 2
    ACTION_PROPOSED = 3
    ACTION_EXECUTED = 4
    ACTION_REJECTED = 5
    MEMORY_WRITE = 6
    MEMORY_READ  = 7
    MESSAGE_SENT = 8
    HUMAN_FEEDBACK = 9
    SYSTEM_END = 10