from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    status: str
    source: str
    message: str
    detections: list[dict[str, Any]] = field(default_factory=list)
    tracks: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)


class AnalysisPipeline:
    def analyze(self, source: str | Path) -> PipelineResult:
        return PipelineResult(
            status="not_ready",
            source=str(source),
            message="Detection model is not loaded",
        )
