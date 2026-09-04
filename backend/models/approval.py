from enum import Enum
from pydantic import BaseModel

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class MCPActionResult(BaseModel):
    action_name: str
    status: str                         # success / failed
    message: str
    timestamp: str
