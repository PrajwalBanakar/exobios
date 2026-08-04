from pydantic import BaseModel
from uuid import UUID
from .state_object import StateObject

class AssessmentResponse(BaseModel):
    assessment_id: UUID
    assesment: StateObject