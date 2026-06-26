from algorithm.pipeline import run_video_analysis, PipelineResult


def test_pipeline_reports_model_not_loaded():
    result = run_video_analysis(
        video_path="demo.mp4",
        output_dir="outputs/task_1/",
        roi={"x": 0, "y": 0, "width": 100, "height": 100},
        settings={"detect_confidence": 0.5},
    )

    assert result == PipelineResult(
        status="not_ready",
        error_message="Detection model is not loaded",
    )


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
