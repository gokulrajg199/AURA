from pydantic import BaseModel, Field
from typing import Any


class AURAProject(BaseModel):
    project_id: str
    project_name: str
    original_idea: str

    status: str = "created"
    current_stage: str = "understand"

    domain: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    research: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] = Field(default_factory=dict)
    innovation: dict[str, Any] = Field(default_factory=dict)
    solution: dict[str, Any] = Field(default_factory=dict)
    architecture: dict[str, Any] = Field(default_factory=dict)
    development: dict[str, Any] = Field(default_factory=dict)
    experiments: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    deliverables: dict[str, Any] = Field(default_factory=dict)

    memory: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
