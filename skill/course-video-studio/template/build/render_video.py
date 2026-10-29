# -*- coding: utf-8 -*-
"""Render built lessons and deliver them: silent HyperFrames render -> mux narration -> thumbnail.

    python -X utf8 render_video.py m1l1 [...|all] [--force]
    python -X utf8 render_video.py m1l1 --draft     (fast low-quality preview -> qc/draft_<id>.mp4)

Output: סרטונים/<module dir>/<num> - <title>.mp4 (+ .jpg). Captions are burned into the picture (karaoke),
so no sidecar subtitle file is written: players auto-load a same-name .srt and would show captions twice. Skips lessons already delivered
unless --force. Every delivery is checked: duration matches the audio, 1920x1080, an audio stream exists.
"""
import json
import subprocess
import sys

from course import ENGINE, OUT, VIDEOS, lesson_ids, lesson_meta

HF = "hyperframes@0.8.106"
DRAFT_FPS = 15
THUMB_AT = 2.8
BAD_CHARS = set('<>"/\\|?*')


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"command failed: {cmd}\n{(r.stdout + r.stderr)[-1500:]}")
    return r.stdout


def probe(path):
    out = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)])
    return json.loads(out)


def out_paths(lid):
    meta = lesson_meta(lid)
    folder = OUT / meta["module"]["dir"]
    folder.mkdir(parents=True, exist_ok=True)
    title = meta["title"].replace(":", " -")
    title = "".join(ch for ch in title if ch not in BAD_CHARS).strip()
    base = f'{meta["num"]} - {title}'
    return tuple(folder / f"{base}{ext}" for ext in (".mp4", ".jpg"))


def deliver(lid, force):
    mp4, jpg = out_paths(lid)
    if mp4.exists() and not force:
        print(f"[{lid}] already delivered: {mp4.name}")
        return True
    clip = VIDEOS / lid / "clip"
    if not (VIDEOS / lid / "build" / "BUILD_OK").exists():
        print(f"[{lid}] SKIPPED: not built (run build_video.py {lid})", flush=True)
        return False
    silent = clip / "renders" / "video.mp4"
    print(f"[{lid}] rendering...", flush=True)
    sh(f"npx --yes {HF} render -o renders/video.mp4 --fps 30 --crf 20 > render.log 2>&1", cwd=str(clip))
    audio = clip / "assets" / "audio" / "lesson.m4a"
    mux(lid, silent, audio, mp4)
    sh(["ffmpeg", "-y", "-v", "error", "-ss", str(THUMB_AT), "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(jpg)])
    info, a = probe(mp4), probe(audio)
    dur, adur = float(info["format"]["duration"]), float(a["format"]["duration"])
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    ok = abs(dur - adur) < 0.6 and (v["width"], v["height"]) == (1920, 1080) and any(
        s["codec_type"] == "audio" for s in info["streams"])
    print(f"[{lid}] {'OK' if ok else 'CHECK FAILED'} {mp4.name} {dur:.1f}s (audio {adur:.1f}s) "
          f"{mp4.stat().st_size / 1e6:.1f}MB", flush=True)
    if ok:
        cleanup(clip)
    return ok


def sfx_track(lid, audio):
    """Mix the lesson's sound events (build/sfx.json, written by the engine) into one WAV, or None."""
    events = VIDEOS / lid / "build" / "sfx.json"
    if not events.exists():
        return None
    if str(ENGINE) not in sys.path:
        sys.path.insert(0, str(ENGINE))
    import sfx
    total = float(probe(audio)["format"]["duration"])
    return sfx.build_track(json.loads(events.read_text(encoding="utf-8")), total, VIDEOS / lid / "clip" / "renders" / "sfx.wav")


def mux(lid, silent, audio, out):
    """Picture + narration, with the soft effects mixed under the voice when they exist."""
    fx = sfx_track(lid, audio)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio)]
    if fx:
        cmd += ["-i", str(fx), "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.8:level=false[a]", "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    sh(cmd + ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)])


def cleanup(clip):
    """Rendering leaves heavy intermediates (silent video, effects track); the delivered MP4 is all we keep."""
    for f in (clip / "renders").glob("*"):
        if f.is_file():
            f.unlink()


def draft(lid):
    """Fast low-quality preview for checking fixes: build/qc/draft_<id>.mp4, never delivered."""
    clip = VIDEOS / lid / "clip"
    sh(f"npx --yes {HF} render -o renders/draft.mp4 --fps {DRAFT_FPS} --quality draft > render.log 2>&1", cwd=str(clip))
    out = VIDEOS.parent / "qc" / f"draft_{lid}.mp4"
    out.parent.mkdir(exist_ok=True)
    mux(lid, clip / "renders" / "draft.mp4", clip / "assets" / "audio" / "lesson.m4a", out)
    cleanup(clip)
    print(f"[{lid}] draft: {out}", flush=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--draft" in sys.argv:
        for lid in lesson_ids(args):
            draft(lid)
        return
    res = [deliver(lid, "--force" in sys.argv) for lid in lesson_ids(args)]
    print("RENDER ALL OK" if all(res) else "SOME RENDERS FAILED")


if __name__ == "__main__":
    main()
