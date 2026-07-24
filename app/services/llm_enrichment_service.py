from collections.abc import Callable
from pathlib import Path

from app.services.model_common import ModelExecutionStatus

ReportEnhancer = Callable[[dict], str]


class LLMEnrichmentService:
    """Optional adapter boundary; it never replaces the deterministic report."""

    def __init__(
        self,
        model_path: str | None = None,
        enhancer: ReportEnhancer | None = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.enhancer = enhancer

    def is_available(self) -> bool:
        return bool(self.model_path and self.model_path.is_file() and self.enhancer)

    def enrich(self, deterministic_report: dict) -> dict:
        if not self.is_available():
            return {
                "status": ModelExecutionStatus.MODEL_NOT_AVAILABLE,
                "enriched_text": None,
            }
        try:
            text = self.enhancer(deterministic_report)  # type: ignore[misc]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Empty LLM response")
            return {
                "status": ModelExecutionStatus.COMPLETED,
                "enriched_text": text.strip(),
            }
        except Exception:
            return {"status": ModelExecutionStatus.FAILED, "enriched_text": None}
