from enum import Enum


class AURAStage(str, Enum):
    UNDERSTAND = "understand"
    INVESTIGATE = "investigate"
    ANALYZE = "analyze"
    VERDICT = "verdict"
    INNOVATE = "innovate"
    SOLUTION = "solution"
    ARCHITECT = "architect"
    BUILD = "build"
    EXPERIMENT = "experiment"
    VALIDATE = "validate"
    DELIVER = "deliver"


STAGE_ORDER = [
    AURAStage.UNDERSTAND,
    AURAStage.INVESTIGATE,
    AURAStage.ANALYZE,
    AURAStage.VERDICT,
    AURAStage.INNOVATE,
    AURAStage.SOLUTION,
    AURAStage.ARCHITECT,
    AURAStage.BUILD,
    AURAStage.EXPERIMENT,
    AURAStage.VALIDATE,
    AURAStage.DELIVER,
]
