# -*- coding: utf-8 -*-
"""Pack skill/course-video-studio into course-video-studio.tar.gz (deterministic: sorted, fixed mtime/owner).

    python pack.py
"""
import gzip
import io
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "course-video-studio"
SRC = ROOT / "skill" / NAME
OUT = ROOT / f"{NAME}.tar.gz"
SKIP = {"__pycache__", ".DS_Store"}
MTIME = 1_700_000_000


def files():
    return sorted(p for p in SRC.rglob("*") if p.is_file() and not SKIP & set(p.parts))


def add(tar, path):
    info = tarfile.TarInfo(f"{NAME}/{path.relative_to(SRC).as_posix()}")
    data = path.read_bytes()
    info.size, info.mtime, info.mode = len(data), MTIME, 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    tar.addfile(info, io.BytesIO(data))


def main():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in files():
            add(tar, p)
    with gzip.GzipFile(OUT, "wb", mtime=MTIME) as gz:
        gz.write(buf.getvalue())
    print(f"{OUT.name}: {len(files())} files, {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
