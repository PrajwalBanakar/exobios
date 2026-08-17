from pydantic import BaseModel, Field


class SupportingCitation(BaseModel):
    # serialization_alias only (not `alias`/`alias_generator`) so this stays
    # camelCase on the wire (matches the documented Spring Boot contract —
    # docs/api/ai-service-contract.md: "camelCase JSON") without touching
    # validation: the LLM-facing JSON schema and model_validate_json() both
    # still key on the snake_case field name, unaffected. See
    # schemas/response.py for where this is exercised.
    chunk_id: str = Field(serialization_alias="chunkId")
    document_id: str = Field(serialization_alias="documentId")
    excerpt: str
    heading: str
    page: int
