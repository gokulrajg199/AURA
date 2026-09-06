from pydantic import BaseModel


class AURAConfig(BaseModel):
    name: str = "AURA"
    version: str = "1.0.0"
    description: str = (
        "AI Research, Innovation & Development Operating System"
    )

    literature_year_from: int = 2022
    literature_year_to: int = 2026
    default_max_papers: int = 20

    evidence_required: bool = True
    project_memory_enabled: bool = True
    human_approval_enabled: bool = True


aura_config = AURAConfig()
