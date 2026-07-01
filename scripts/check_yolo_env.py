"""Check local YOLOv11 inference environment."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any


PACKAGE_IMPORTS = {
    "ultralytics": "ultralytics",
    "opencv-python": "cv2",
    "torch": "torch",
}


def detect_package(package_name: str, import_name: str | None = None) -> dict[str, Any]:
    import_name = import_name or package_name
    installed = importlib.util.find_spec(import_name) is not None
    version = None
    if installed:
        try:
            version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {"installed": installed, "version": version}


def build_report() -> dict[str, Any]:
    packages = {
        import_name: detect_package(package_name, import_name)
        for package_name, import_name in PACKAGE_IMPORTS.items()
    }
    cuda_available = None
    if packages["torch"]["installed"]:
        import torch

        cuda_available = bool(torch.cuda.is_available())

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
        "cuda_available": cuda_available,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check YOLOv11 local environment")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    report = build_report()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
