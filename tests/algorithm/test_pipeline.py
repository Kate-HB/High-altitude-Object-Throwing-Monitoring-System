from algorithm.pipeline import AnalysisPipeline, PipelineResult


def test_pipeline_reports_model_not_loaded():
    result = AnalysisPipeline().analyze("demo.mp4")

    assert result == PipelineResult(
        status="not_ready",
        source="demo.mp4",
        message="Detection model is not loaded",
        detections=[],
        tracks=[],
        events=[],
    )
