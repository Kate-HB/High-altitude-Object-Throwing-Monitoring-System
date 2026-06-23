from algorithm.pipeline import AnalysisPipeline, PipelineResult


def test_pipeline_reports_model_not_loaded():
    result = AnalysisPipeline().analyze(
        "demo.mp4",
        roi=[(0, 0), (100, 0), (100, 100), (0, 100)],
        detection_params={"confidence": 0.5},
    )

    assert result == PipelineResult(
        status="not_ready",
        source="demo.mp4",
        message="Detection model is not loaded",
        current_frame=None,
        detections=[],
        tracks=[],
        events=[],
    )
