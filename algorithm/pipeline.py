from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    status: str
    source: str
    message: str
    current_frame: Any | None = None
    detections: list[dict[str, Any]] = field(default_factory=list)
    tracks: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)


class AnalysisPipeline:
    def analyze(
        self,
        source: str | Path,
        roi: list[tuple[int, int]] | None = None,
        detection_params: dict[str, Any] | None = None,
    ) -> PipelineResult:
        return PipelineResult(
            status="not_ready",
            source=str(source),
            message="Detection model is not loaded",
        )
