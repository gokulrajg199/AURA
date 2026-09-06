"""
AURA — Autonomous Project Orchestrator

Purpose:
    Connect all AURA agents into one autonomous project lifecycle
    while continuously providing the latest Project Memory context
    to every stage.

Pipeline:

    UNDERSTAND
        ↓
    INVESTIGATE
        ↓
    ANALYZE
        ↓
    VERDICT
        ↓
    INNOVATE
        ↓
    SOLUTION
        ↓
    ARCHITECT
        ↓
    BUILD
        ↓
    EXPERIMENT
        ↓
    VALIDATE
        ↓
    DELIVER

AURA principle:

    ONE IDEA
        ↓
    CONTINUOUS PROJECT MEMORY
        ↓
    EVIDENCE + REASONING
        ↓
    CONNECTED DEVELOPMENT LIFECYCLE
        ↓
    FINAL DELIVERABLES

Important:
    The orchestrator does not fabricate research, experiments,
    validation results, or evidence.

    Each agent remains responsible for its own reasoning and
    evidence generation.

    Project Memory acts as the persistent context layer connecting
    decisions, findings, uncertainties, conflicts, and evidence
    throughout the complete AURA lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agents.idea_intelligence import idea_intelligence_agent
from agents.investigation import investigation_agent
from agents.analysis import analysis_agent
from agents.verdict import verdict_agent
from agents.innovation import innovation_agent
from agents.solution import solution_agent
from agents.architect import architect_agent
from agents.build import build_agent
from agents.experiment import experiment_agent
from agents.validation import validation_agent
from agents.delivery import delivery_agent

from memory.project_memory import (
    add_memory,
    build_project_context,
)

from models.project import AURAProject

from orchestration.contract import (
    AURAStageContract,
)

from orchestration.stages import (
    AURAStage,
    STAGE_ORDER,
)


class AURAOrchestrator:
    """
    Main controller for the AURA autonomous project pipeline.

    Responsibilities:

        1. Create projects.
        2. Execute the 11-stage lifecycle.
        3. Maintain project status.
        4. Maintain current stage.
        5. Record lifecycle events.
        6. Refresh Project Memory context before every stage.
        7. Expose frontend-friendly pipeline state.
        8. Support resume and partial execution.

    Project Memory is deliberately handled at the orchestration
    layer so that every agent receives the latest connected context
    without changing the public run() contract of individual agents.
    """

    def __init__(self) -> None:
        self.contracts: dict[
            AURAStage,
            AURAStageContract,
        ] = {
            AURAStage.UNDERSTAND: AURAStageContract(
                AURAStage.UNDERSTAND,
                idea_intelligence_agent.run,
            ),

            AURAStage.INVESTIGATE: AURAStageContract(
                AURAStage.INVESTIGATE,
                investigation_agent.run,
            ),

            AURAStage.ANALYZE: AURAStageContract(
                AURAStage.ANALYZE,
                analysis_agent.run,
            ),

            AURAStage.VERDICT: AURAStageContract(
                AURAStage.VERDICT,
                verdict_agent.run,
            ),

            AURAStage.INNOVATE: AURAStageContract(
                AURAStage.INNOVATE,
                innovation_agent.run,
            ),

            AURAStage.SOLUTION: AURAStageContract(
                AURAStage.SOLUTION,
                solution_agent.run,
            ),

            AURAStage.ARCHITECT: AURAStageContract(
                AURAStage.ARCHITECT,
                architect_agent.run,
            ),

            AURAStage.BUILD: AURAStageContract(
                AURAStage.BUILD,
                build_agent.run,
            ),

            AURAStage.EXPERIMENT: AURAStageContract(
                AURAStage.EXPERIMENT,
                experiment_agent.run,
            ),

            AURAStage.VALIDATE: AURAStageContract(
                AURAStage.VALIDATE,
                validation_agent.run,
            ),

            AURAStage.DELIVER: AURAStageContract(
                AURAStage.DELIVER,
                delivery_agent.run,
            ),
        }

    # ============================================================
    # PROJECT CREATION
    # ============================================================

    def create_project(
        self,
        idea: str,
        project_name: str | None = None,
    ) -> AURAProject:
        """
        Create a new AURA project from one user idea.
        """

        clean_idea = idea.strip()

        if not clean_idea:
            raise ValueError(
                "AURA requires a project idea."
            )

        clean_name = (
            project_name.strip()
            if project_name
            else self._generate_project_name(
                clean_idea
            )
        )

        project = AURAProject(
            project_id=self._generate_project_id(),
            project_name=clean_name,
            original_idea=clean_idea,
            status="created",
            current_stage=AURAStage.UNDERSTAND.value,
        )

        add_memory(
            project=project,
            stage=AURAStage.UNDERSTAND.value,
            event="project_created",
            data={
                "project_id": project.project_id,
                "project_name": project.project_name,
                "original_idea": project.original_idea,
            },
        )

        self._refresh_memory_context(
            project
        )

        return project

    # ============================================================
    # PROJECT MEMORY CONTEXT
    # ============================================================

    def _refresh_memory_context(
        self,
        project: AURAProject,
    ) -> None:
        """
        Refresh the connected Project Memory context.

        This creates a current snapshot of:

            - recent decisions
            - findings
            - uncertainties
            - conflicts
            - evidence
            - recent project events
            - stage-specific memory
            - project-level memory summary

        The snapshot is placed inside project.analysis so existing
        agents can access it without changing the AURAProject schema
        or the run() signature of every agent.

        The context is refreshed immediately before every stage and
        after important lifecycle events.
        """

        try:
            context = build_project_context(
                project
            )

            if not isinstance(
                context,
                dict,
            ):
                context = {}

            project.analysis[
                "project_memory_context"
            ] = context

        except Exception as error:
            # Memory context must never destroy the main pipeline.
            project.analysis[
                "project_memory_context"
            ] = {
                "available": False,
                "error": str(error),
            }

    # ============================================================
    # RUN COMPLETE PIPELINE
    # ============================================================

    async def run(
        self,
        project: AURAProject,
        start_stage: AURAStage = AURAStage.UNDERSTAND,
        stop_on_failure: bool = True,
    ) -> AURAProject:
        """
        Execute the AURA pipeline from the selected stage.

        Default:

            UNDERSTAND
                →
            INVESTIGATE
                →
            ANALYZE
                →
            VERDICT
                →
            INNOVATE
                →
            SOLUTION
                →
            ARCHITECT
                →
            BUILD
                →
            EXPERIMENT
                →
            VALIDATE
                →
            DELIVER
        """

        if not project.original_idea.strip():
            project.status = "failed"

            add_memory(
                project=project,
                stage=start_stage.value,
                event="pipeline_failed",
                data={
                    "reason": "Empty project idea.",
                },
            )

            self._refresh_memory_context(
                project
            )

            return project

        try:
            start_index = STAGE_ORDER.index(
                start_stage
            )

        except ValueError:
            project.status = "failed"

            add_memory(
                project=project,
                stage=str(start_stage),
                event="pipeline_failed",
                data={
                    "reason": "Invalid starting stage.",
                },
            )

            self._refresh_memory_context(
                project
            )

            return project

        project.status = "running"

        add_memory(
            project=project,
            stage=start_stage.value,
            event="pipeline_started",
            data={
                "start_stage": start_stage.value,
                "stop_on_failure": stop_on_failure,
            },
        )

        self._refresh_memory_context(
            project
        )

        for stage in STAGE_ORDER[start_index:]:
            result = await self.execute_stage(
                project=project,
                stage=stage,
            )

            if not result.success:
                project.status = "failed"

                add_memory(
                    project=project,
                    stage=stage.value,
                    event="stage_failed",
                    data={
                        "message": result.message,
                    },
                )

                self._refresh_memory_context(
                    project
                )

                if stop_on_failure:
                    break

                continue

            add_memory(
                project=project,
                stage=stage.value,
                event="stage_completed",
                data={
                    "message": result.message,
                    "next_stage": (
                        result.next_stage.value
                        if result.next_stage
                        else None
                    ),
                },
            )

            self._refresh_memory_context(
                project
            )

            if stage == AURAStage.DELIVER:
                project.status = "completed"
                project.current_stage = (
                    AURAStage.DELIVER.value
                )

                add_memory(
                    project=project,
                    stage=stage.value,
                    event="pipeline_completed",
                    data={
                        "completed_at": self._timestamp(),
                    },
                )

                self._refresh_memory_context(
                    project
                )

                break

            next_stage = result.next_stage

            if next_stage is None:
                next_stage = self._next_stage(
                    stage
                )

            if next_stage is None:
                project.status = "completed"

                add_memory(
                    project=project,
                    stage=stage.value,
                    event="pipeline_completed",
                    data={
                        "completed_at": self._timestamp(),
                    },
                )

                self._refresh_memory_context(
                    project
                )

                break

            project.current_stage = (
                next_stage.value
            )

        if project.status == "running":
            project.status = "completed"

        self._refresh_memory_context(
            project
        )

        return project

    # ============================================================
    # EXECUTE ONE STAGE
    # ============================================================

    async def execute_stage(
        self,
        project: AURAProject,
        stage: AURAStage,
    ):
        """
        Execute exactly one AURA stage.

        Project Memory is refreshed immediately before the agent
        executes, ensuring that the stage receives the latest
        connected project context.
        """

        contract = self.contracts.get(
            stage
        )

        if contract is None:
            from orchestration.contract import (
                AURAStageResult,
            )

            return AURAStageResult(
                stage=stage,
                success=False,
                message=(
                    f"No agent is registered for "
                    f"stage '{stage.value}'."
                ),
            )

        project.current_stage = (
            stage.value
        )

        # --------------------------------------------------------
        # Refresh memory BEFORE the agent runs.
        # --------------------------------------------------------

        self._refresh_memory_context(
            project
        )

        add_memory(
            project=project,
            stage=stage.value,
            event="stage_started",
            data={
                "started_at": self._timestamp(),
                "memory_context_available": (
                    "project_memory_context"
                    in project.analysis
                ),
            },
        )

        # Refresh once more so the stage-start event itself becomes
        # part of the context available to the agent.
        self._refresh_memory_context(
            project
        )

        try:
            result = await contract.execute(
                project
            )

            # ----------------------------------------------------
            # Refresh after the agent finishes so its findings,
            # evidence, decisions and uncertainties become part
            # of the shared context for the next stage.
            # ----------------------------------------------------

            self._refresh_memory_context(
                project
            )

            return result

        except Exception as error:
            from orchestration.contract import (
                AURAStageResult,
            )

            add_memory(
                project=project,
                stage=stage.value,
                event="stage_exception",
                data={
                    "error": str(error),
                },
            )

            self._refresh_memory_context(
                project
            )

            return AURAStageResult(
                stage=stage,
                success=False,
                message=(
                    f"Stage '{stage.value}' failed: "
                    f"{error}"
                ),
            )

    # ============================================================
    # RESUME PIPELINE
    # ============================================================

    async def resume(
        self,
        project: AURAProject,
        stop_on_failure: bool = True,
    ) -> AURAProject:
        """
        Resume the project from its current stage.
        """

        try:
            current_stage = AURAStage(
                project.current_stage
            )

        except ValueError:
            current_stage = (
                AURAStage.UNDERSTAND
            )

        add_memory(
            project=project,
            stage=current_stage.value,
            event="pipeline_resumed",
            data={
                "resume_stage": current_stage.value,
            },
        )

        self._refresh_memory_context(
            project
        )

        return await self.run(
            project=project,
            start_stage=current_stage,
            stop_on_failure=stop_on_failure,
        )

    # ============================================================
    # RUN UNTIL A SPECIFIC STAGE
    # ============================================================

    async def run_until(
        self,
        project: AURAProject,
        target_stage: AURAStage,
        stop_on_failure: bool = True,
    ) -> AURAProject:
        """
        Run the pipeline from the current stage until
        the requested target stage.
        """

        try:
            start_index = STAGE_ORDER.index(
                AURAStage(
                    project.current_stage
                )
            )

        except ValueError:
            start_index = 0

        try:
            target_index = STAGE_ORDER.index(
                target_stage
            )

        except ValueError:
            project.status = "failed"

            add_memory(
                project=project,
                stage=project.current_stage,
                event="pipeline_failed",
                data={
                    "reason": (
                        f"Unknown target stage: "
                        f"{target_stage}"
                    ),
                },
            )

            self._refresh_memory_context(
                project
            )

            return project

        if target_index < start_index:
            project.status = "failed"

            add_memory(
                project=project,
                stage=project.current_stage,
                event="pipeline_failed",
                data={
                    "reason": (
                        "Target stage occurs before "
                        "the current stage."
                    ),
                },
            )

            self._refresh_memory_context(
                project
            )

            return project

        project.status = "running"

        self._refresh_memory_context(
            project
        )

        for index in range(
            start_index,
            target_index + 1,
        ):
            stage = STAGE_ORDER[index]

            result = await self.execute_stage(
                project=project,
                stage=stage,
            )

            if not result.success:
                project.status = "failed"

                self._refresh_memory_context(
                    project
                )

                if stop_on_failure:
                    return project

            if stage == target_stage:
                project.current_stage = (
                    stage.value
                )

                add_memory(
                    project=project,
                    stage=stage.value,
                    event="target_stage_reached",
                    data={
                        "target_stage": stage.value,
                    },
                )

                project.status = (
                    "paused"
                    if stage
                    != AURAStage.DELIVER
                    else "completed"
                )

                self._refresh_memory_context(
                    project
                )

                return project

        self._refresh_memory_context(
            project
        )

        return project

    # ============================================================
    # PIPELINE STATUS
    # ============================================================

    def get_pipeline_status(
        self,
        project: AURAProject,
    ) -> dict[str, Any]:
        """
        Return a frontend-friendly representation
        of the complete AURA pipeline.
        """

        current_stage = project.current_stage

        try:
            current_index = STAGE_ORDER.index(
                AURAStage(current_stage)
            )

        except ValueError:
            current_index = 0

        stages = []

        for index, stage in enumerate(
            STAGE_ORDER
        ):
            if project.status == "completed":
                status = "completed"

            elif index < current_index:
                status = "completed"

            elif index == current_index:
                status = "current"

            else:
                status = "pending"

            stages.append(
                {
                    "order": index + 1,
                    "stage": stage.value,
                    "label": self._stage_label(
                        stage
                    ),
                    "status": status,
                }
            )

        completed_count = sum(
            1
            for stage in stages
            if stage["status"] == "completed"
        )

        progress = round(
            completed_count
            / len(STAGE_ORDER)
            * 100,
            1,
        )

        return {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "status": project.status,
            "current_stage": current_stage,
            "progress": progress,
            "completed_stages": completed_count,
            "total_stages": len(STAGE_ORDER),
            "stages": stages,
        }

    # ============================================================
    # PROJECT SNAPSHOT
    # ============================================================

    def get_project_snapshot(
        self,
        project: AURAProject,
    ) -> dict[str, Any]:
        """
        Return the complete project state in a
        frontend/API-friendly structure.
        """

        self._refresh_memory_context(
            project
        )

        return {
            "project": {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "original_idea": project.original_idea,
                "status": project.status,
                "current_stage": project.current_stage,
                "domain": project.domain,
            },

            "understanding": {
                "objectives": project.objectives,
                "requirements": project.requirements,
                "analysis": project.analysis.get(
                    "problem_understanding",
                    {},
                ),
            },

            "research": project.research,

            "analysis": project.analysis,

            "innovation": project.innovation,

            "solution": project.solution,

            "architecture": project.architecture,

            "development": project.development,

            "experiments": project.experiments,

            "validation": project.validation,

            "deliverables": project.deliverables,

            "memory": project.memory,

            "evidence": project.evidence,

            "pipeline": self.get_pipeline_status(
                project
            ),
        }

    # ============================================================
    # STAGE HELPERS
    # ============================================================

    def _next_stage(
        self,
        current_stage: AURAStage,
    ) -> AURAStage | None:
        try:
            index = STAGE_ORDER.index(
                current_stage
            )

        except ValueError:
            return None

        if index + 1 >= len(
            STAGE_ORDER
        ):
            return None

        return STAGE_ORDER[index + 1]

    def _stage_label(
        self,
        stage: AURAStage,
    ) -> str:
        labels = {
            AURAStage.UNDERSTAND:
                "Understand Idea",

            AURAStage.INVESTIGATE:
                "Investigate",

            AURAStage.ANALYZE:
                "Analyze Research",

            AURAStage.VERDICT:
                "AURA Verdict",

            AURAStage.INNOVATE:
                "Innovation",

            AURAStage.SOLUTION:
                "Solution Design",

            AURAStage.ARCHITECT:
                "System Architecture",

            AURAStage.BUILD:
                "Development",

            AURAStage.EXPERIMENT:
                "Experiments",

            AURAStage.VALIDATE:
                "Validation",

            AURAStage.DELIVER:
                "Final Delivery",
        }

        return labels.get(
            stage,
            stage.value.replace(
                "_",
                " ",
            ).title(),
        )

    # ============================================================
    # ID / TIME HELPERS
    # ============================================================

    def _generate_project_id(
        self,
    ) -> str:
        return (
            "aura-"
            + uuid4().hex[:12]
        )

    def _generate_project_name(
        self,
        idea: str,
    ) -> str:
        words = [
            word.strip(
                ".,:;!?()[]{}"
            )
            for word in idea.split()
        ]

        words = [
            word
            for word in words
            if word
        ]

        if not words:
            return "AURA Project"

        # Preserve the full user idea as the default project title.
        # Truncate only for an extreme UI/storage edge case.
        name = " ".join(words)
        return name[:120]

    def _timestamp(
        self,
    ) -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()


aura_orchestrator = AURAOrchestrator()