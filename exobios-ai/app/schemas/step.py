from enum import Enum
from typing import Any

from pydantic import BaseModel


class StepStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    
    
class StepResult(BaseModel):
    step_name: str
    status:StepStatus
    data: dict[str, Any] | None = None
    error_message: str | None = None