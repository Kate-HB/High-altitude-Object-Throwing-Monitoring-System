import tempfile
from pathlib import Path

from algorithm.pipeline import run_video_analysis, PipelineResult

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEMO_VIDEO = _PROJECT_ROOT / "data" / "videos" / "demo.mp4"
_MODEL = _PROJECT_ROOT / "models" / "best.onnx"


def test_pipeline_reports_video_not_found():
    result = run_video_analysis(
        video_path="nonexistent_video.mp4",
        output_dir="outputs/task_1/",
        roi={"x": 0, "y": 0, "width": 100, "height": 100},
        settings={"detect_confidence": 0.5},
    )

    assert result.status == "failed"
    assert "视频" in result.error_message


def test_run_video_analysis_returns_all_fields():
    """Verify PipelineResult includes all contract fields (Section 4 of algorithm-interface.md)."""
    result = run_video_analysis(
        video_path="demo.mp4",
        output_dir="outputs/task_1/",
        roi={"x": 0, "y": 0, "width": 100, "height": 100},
        settings={},
    )

    assert hasattr(result, "status")
    assert hasattr(result, "total_frames")
    assert hasattr(result, "processed_frames")
    assert hasattr(result, "result_video_path")
    assert hasattr(result, "events")
    assert hasattr(result, "detection_results")
    assert hasattr(result, "tracking_results")
    assert hasattr(result, "error_message")


def test_pipeline_with_real_video():
    """Full end-to-end pipeline run with real demo video and model."""
    assert _DEMO_VIDEO.is_file(), f"Demo video not found: {_DEMO_VIDEO}"
    assert _MODEL.is_file(), f"Model not found: {_MODEL}"

    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_video_analysis(
            video_path=str(_DEMO_VIDEO),
            output_dir=tmpdir,
            roi={"x": 100, "y": 50, "width": 800, "height": 500},
            settings={"detect_confidence": 0.35, "imgsz": 960},
            model_path=str(_MODEL),
            device="cpu",
        )

        assert result.status == "success", f"Pipeline failed: {result.error_message}"
        assert result.total_frames > 0
        assert result.processed_frames > 0
        assert result.processed_frames <= result.total_frames
        assert result.result_video_path is not None
        assert Path(result.result_video_path).is_file()
        assert isinstance(result.events, list)
        assert isinstance(result.detection_results, list)
        assert isinstance(result.tracking_results, list)
