import importlib.util
from pathlib import Path


def load_check_yolo_env_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_yolo_env.py"
    spec = importlib.util.spec_from_file_location("check_yolo_env", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detect_package_reports_missing_module():
    module = load_check_yolo_env_module()

    result = module.detect_package("package_that_should_not_exist_20260624")

    assert result["installed"] is False
    assert result["version"] is None


def test_build_report_contains_required_algorithm_packages():
    module = load_check_yolo_env_module()

    report = module.build_report()

    assert "python" in report
    assert "packages" in report
    assert "ultralytics" in report["packages"]
    assert "cv2" in report["packages"]
    assert "torch" in report["packages"]
