"""Zip helpers for moving one experiment folder between machines (Phase 14b).

A remote compute server (College GPU / Colab) runs core/ against ITS OWN
``experiments/<id>/`` folder. To make that work the Mac sends the folder up
before a run and brings it back afterwards, as a base64 zip inside the same
JSON protocol the other calls use.

Both directions go through ``unpack_b64_into``, which treats the archive as
untrusted: no absolute paths, no ``..``, no symlinks, bounded size.
"""
from __future__ import annotations

import base64
import io
import re
import shutil
import stat
import zipfile
from pathlib import Path

EXPERIMENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
MAX_UNPACKED_BYTES = 4 * 1024**3
MAX_MEMBERS = 5000


def validate_experiment_id(experiment_id: object) -> str:
    if not isinstance(experiment_id, str) or not EXPERIMENT_ID_RE.match(experiment_id) or ".." in experiment_id:
        raise ValueError("Invalid experiment id.")
    return experiment_id


def pack_dir_b64(directory: Path) -> str:
    if not directory.is_dir():
        raise FileNotFoundError(f"Experiment folder not found: {directory.name}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not path.is_symlink():
                archive.write(path, path.relative_to(directory).as_posix())
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def unpack_b64_into(archive_b64: str, directory: Path) -> int:
    """Extract into `directory` (created if needed), overwriting files with
    the same name. Returns the number of files written."""
    try:
        raw = base64.b64decode(archive_b64, validate=True)
    except Exception:
        raise ValueError("Archive is not valid base64.") from None
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise ValueError("Archive is not a valid zip file.") from None

    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_MEMBERS:
            raise ValueError("Archive has too many files.")
        if sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
            raise ValueError("Archive is too large when unpacked.")

        directory.mkdir(parents=True, exist_ok=True)
        root = directory.resolve()
        planned: list[tuple[zipfile.ZipInfo, Path]] = []
        for info in infos:
            if info.is_dir():
                continue
            name = info.filename
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Archive contains a symbolic link.")
            if name.startswith(("/", "\\")) or "\\" in name or re.match(r"^[A-Za-z]:", name):
                raise ValueError("Archive contains an unsafe path.")
            target = (root / name).resolve()
            if target == root or root not in target.parents:
                raise ValueError("Archive contains an unsafe path.")
            planned.append((info, target))

        for info, target in planned:
            target.parent.mkdir(parents=True, exist_ok=True)
            written = 0
            with archive.open(info) as source, open(target, "wb") as destination:
                while chunk := source.read(1024 * 1024):
                    written += len(chunk)
                    if written > info.file_size:
                        raise ValueError("Archive entry is larger than it declares.")
                    destination.write(chunk)
    return len(planned)
