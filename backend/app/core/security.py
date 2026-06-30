"""File-path security validators — whitelist + traversal guards."""

import os
from pathlib import Path

# Directories that the file-serving endpoint is allowed to read from
_ALLOWED_DIRS = ("uploads", "outputs", "events/snapshots")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _is_allowed(rel_path: Path) -> bool:
    """Check whether `rel_path` starts with one of the whitelist prefixes.

    Handles multi-component whitelist entries (``events/snapshots``) by
    checking every prefix depth, e.g. for ``events/snapshots/img.jpg`` we
    test ``events`` then ``events/snapshots``.
    """
    parts = rel_path.parts
    for depth in range(1, len(parts) + 1):
        # Normalize to forward slashes so Windows backslashes match the whitelist
        prefix = Path(*parts[:depth]).as_posix()
        if prefix in _ALLOWED_DIRS:
            return True
    return False


def validate_file_path(rel_path: str) -> Path | None:
    """Return the resolved *absolute* path if `rel_path` is safe, else None.

    Rules:
    1. Reject empty or absolute paths.
    2. Reject ``..`` segments.
    3. Resolve symlinks / relative components.
    4. Reject if the resolved path escapes the project root.
    5. Reject if the path does NOT start with a whitelist directory.
    6. Reject if the path does not exist on disk.
    """
    if not rel_path:
        return None

    # Normalize: replace backslashes with forward slashes for URL safety
    rel_path = rel_path.replace("\\", "/")

    p = Path(rel_path)

    # Rule 1 — no absolute paths
    if p.is_absolute():
        return None

    # Rule 2 — reject ".." segments
    if ".." in p.parts:
        return None

    # Rule 3 — resolve to absolute
    resolved = (_PROJECT_ROOT / p).resolve()

    # Rule 4 — must stay inside project root (path-separator-safe check)
    root_str = str(_PROJECT_ROOT.resolve())
    resolved_str = str(resolved)
    if not (resolved_str == root_str or resolved_str.startswith(root_str + os.sep)):
        return None

    # Rule 5 — whitelist prefix check (multi-component aware)
    if not _is_allowed(p):
        return None

    return resolved
