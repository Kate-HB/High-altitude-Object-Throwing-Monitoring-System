import importlib.util
from pathlib import Path


def load_prepare_dataset_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "prepare_dataset.py"
    spec = importlib.util.spec_from_file_location("prepare_dataset", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_dataset_normalizes_labels_and_writes_yolo_layout(tmp_path):
    module = load_prepare_dataset_module()
    source = tmp_path / "source"
    output = tmp_path / "dataset"
    (source / "images").mkdir(parents=True)
    (source / "labels").mkdir()
    (source / "images" / "a.jpg").write_bytes(b"fake-image-a")
    (source / "images" / "b.jpg").write_bytes(b"fake-image-b")
    (source / "labels" / "a.txt").write_text("7 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    (source / "labels" / "b.txt").write_text("3 0.4 0.4 0.1 0.1\n", encoding="utf-8")

    summary = module.prepare_dataset(source, output, val_ratio=0.5)

    assert summary["total_images"] == 2
    assert summary["train_images"] == 1
    assert summary["val_images"] == 1
    assert (output / "images" / "train" / "a.jpg").exists()
    assert (output / "images" / "val" / "b.jpg").exists()
    assert (output / "labels" / "train" / "a.txt").read_text(encoding="utf-8") == "0 0.5 0.5 0.2 0.2\n"
    assert (output / "labels" / "val" / "b.txt").read_text(encoding="utf-8") == "0 0.4 0.4 0.1 0.1\n"
    assert "falling_object" in (output / "data.yaml").read_text(encoding="utf-8")


def test_prepare_dataset_creates_empty_label_for_unlabeled_image(tmp_path):
    module = load_prepare_dataset_module()
    source = tmp_path / "source"
    output = tmp_path / "dataset"
    (source / "images").mkdir(parents=True)
    (source / "labels").mkdir()
    (source / "images" / "unlabeled.png").write_bytes(b"fake-image")

    summary = module.prepare_dataset(source, output, val_ratio=0)

    assert summary["missing_labels"] == 1
    assert (output / "labels" / "train" / "unlabeled.txt").read_text(encoding="utf-8") == ""
