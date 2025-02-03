from enum import Enum

class MonitorStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    RATE_LIMITED = "RATE_LIMITED"
    ERROR = "ERROR"
    INITIALIZING = "INITIALIZING"
