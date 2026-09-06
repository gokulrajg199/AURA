from __future__ import annotations

from inspect import isawaitable
from typing import Any, Awaitable, Callable

from models.project import AURAProject
from orchestration.stages import AURAStage


StageHandler = Callable[
    [AURAProject],
    "AURAStageResult | dict[str, Any] | Awaitable[Any]",
]


class AURAStageResult:
    """
    Standard result returned by every AURA stage.
    """

    def __init__(
        self,
        stage: AURAStage,
        success: bool,
        message: str = "",
        data: dict[str, Any] | None = None,
        next_stage: AURAStage | None = None,
    ) -> None:
        self.stage = stage
        self.success = bool(success)
        self.message = message or ""
        self.data = data or {}
        self.next_stage = next_stage

    def model_dump(self) -> dict[str, Any]:
        """
        Convert the result into a JSON-friendly dictionary.
        """

        return {
            "stage": self.stage.value,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "next_stage": (
                self.next_stage.value
                if self.next_stage
                else None
            ),
        }

    def __repr__(self) -> str:
        return (
            "AURAStageResult("
            f"stage={self.stage.value!r}, "
            f"success={self.success!r}, "
            f"message={self.message!r}, "
            f"next_stage="
            f"{self.next_stage.value if self.next_stage else None!r}"
            ")"
        )


class AURAStageContract:
    """
    Execution wrapper for an AURA agent.

    Supports:

        def run(project):
            return AURAStageResult(...)

    and:

        async def run(project):
            return AURAStageResult(...)

    and agents that return:

        {
            "success": True,
            "stage": "ANALYZE",
            "message": "...",
            "data": {...},
            "next_stage": "VERDICT"
        }
    """

    def __init__(
        self,
        stage: AURAStage,
        handler: StageHandler,
    ) -> None:
        self.stage = stage
        self.handler = handler

    async def execute(
        self,
        project: AURAProject,
    ) -> AURAStageResult:
        """
        Execute the registered stage handler and normalize
        its output into AURAStageResult.
        """

        # Execute the agent.
        result = self.handler(project)

        if isawaitable(result):
            result = await result

        # Convert dictionary / model responses into the
        # standard AURAStageResult format.
        result = self._normalize_result(result)

        # Final validation.
        if not isinstance(result, AURAStageResult):
            raise TypeError(
                f"Agent for stage '{self.stage.value}' "
                "could not be converted into AURAStageResult."
            )

        # Make sure the agent returned the correct stage.
        if result.stage != self.stage:
            raise ValueError(
                f"Stage contract mismatch: expected "
                f"'{self.stage.value}', but agent returned "
                f"'{result.stage.value}'."
            )

        # IMPORTANT:
        # Return the validated result to the orchestrator.
        return result

    def _normalize_result(
        self,
        result: Any,
    ) -> AURAStageResult:
        """
        Convert supported agent responses into AURAStageResult.
        """

        # Already normalized.
        if isinstance(result, AURAStageResult):
            return result

        # Dictionary response.
        if isinstance(result, dict):
            return self._from_dict(result)

        # Pydantic / structured object.
        if hasattr(result, "model_dump"):
            try:
                dumped = result.model_dump()

                if isinstance(dumped, dict):
                    return self._from_dict(dumped)

            except Exception:
                pass

        # Legacy object exposing dict().
        if hasattr(result, "dict"):
            try:
                dumped = result.dict()

                if isinstance(dumped, dict):
                    return self._from_dict(dumped)

            except Exception:
                pass

        raise TypeError(
            f"Agent for stage '{self.stage.value}' "
            f"returned unsupported result type: "
            f"{type(result).__name__}."
        )

    def _from_dict(
        self,
        result: dict[str, Any],
    ) -> AURAStageResult:
        """
        Convert an agent dictionary into AURAStageResult.
        """

        # ---------------------------------------------------------
        # Stage
        # ---------------------------------------------------------

        raw_stage = result.get(
            "stage",
            self.stage.value,
        )

        if isinstance(raw_stage, AURAStage):
            stage = raw_stage

        else:
            try:
                stage = AURAStage(
                    str(raw_stage).lower()
                )

            except ValueError:

                try:
                    stage = AURAStage[
                        str(raw_stage).upper()
                    ]

                except KeyError as exc:
                    raise ValueError(
                        f"Invalid stage returned by agent: "
                        f"{raw_stage!r}"
                    ) from exc

        # ---------------------------------------------------------
        # Success
        # ---------------------------------------------------------

        success = bool(
            result.get(
                "success",
                True,
            )
        )

        # ---------------------------------------------------------
        # Message
        # ---------------------------------------------------------

        message = str(
            result.get(
                "message",
                "",
            )
            or ""
        )

        # ---------------------------------------------------------
        # Data
        # ---------------------------------------------------------

        data = result.get(
            "data",
            {},
        )

        if not isinstance(data, dict):
            data = {
                "result": data
            }

        # ---------------------------------------------------------
        # Preserve additional intelligence
        #
        # Some AURA agents return useful fields outside "data".
        # We preserve them instead of silently losing them.
        # ---------------------------------------------------------

        reserved_keys = {
            "stage",
            "success",
            "message",
            "data",
            "next_stage",
        }

        for key, value in result.items():

            if key in reserved_keys:
                continue

            if key not in data:
                data[key] = value

        # ---------------------------------------------------------
        # Next stage
        # ---------------------------------------------------------

        raw_next_stage = result.get(
            "next_stage"
        )

        next_stage = None

        if raw_next_stage:

            if isinstance(
                raw_next_stage,
                AURAStage,
            ):
                next_stage = raw_next_stage

            else:

                try:
                    next_stage = AURAStage(
                        str(
                            raw_next_stage
                        ).lower()
                    )

                except ValueError:

                    try:
                        next_stage = AURAStage[
                            str(
                                raw_next_stage
                            ).upper()
                        ]

                    except KeyError:
                        # Unknown next stage should not destroy
                        # an otherwise valid result.
                        next_stage = None

        return AURAStageResult(
            stage=stage,
            success=success,
            message=message,
            data=data,
            next_stage=next_stage,
        )


__all__ = [
    "AURAStageResult",
    "AURAStageContract",
    "StageHandler",
]