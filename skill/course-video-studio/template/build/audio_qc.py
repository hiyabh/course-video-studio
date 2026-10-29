# -*- coding: utf-8 -*-
"""Audio QC of delivered lessons: duration, integrated LUFS, true peak, LRA, leading/trailing silence."""
import json, re, subprocess, sys
sys.path.insert(0, ".")
from course import LESSONS, lesson_meta
from render_video import out_paths
rows = []
for lid, _, _, _ in LESSONS:
    mp4 = out_paths(lid)[0]
    if not mp4.exists():
        rows.append({"id": lid, "missing": True}); continue
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    o = r.stderr
    def g(k):
        m = re.search(k + r":\s*(-?[\d.]+)", o.split("Summary:")[-1]); return float(m.group(1)) if m else None
    dur = float(json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(mp4)], capture_output=True, text=True).stdout)["format"]["duration"])
    s = subprocess.run(["ffmpeg", "-nostats", "-i", str(mp4), "-af", "silencedetect=n=-40dB:d=0.8", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", s)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", s)]
    lead = ends[0] if starts and starts[0] < 0.2 and ends else 0.0
    tail = dur - starts[-1] if starts and (not ends or starts[-1] > (ends[-1] if ends else 0)) else 0.0
    gaps = [(a, b - a) for a, b in zip(starts, ends) if b - a > 3.0 and a > 0.5]
    rows.append({"id": lid, "num": lesson_meta(lid)["num"], "dur": round(dur, 1), "lufs": g("I"), "lra": g("LRA"), "peak": g("Peak"), "lead": round(lead, 2), "tail": round(tail, 2), "long_gaps": gaps})
    print(rows[-1], flush=True)
json.dump(rows, open("qc/audio_qc.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL min", round(sum(r.get("dur", 0) for r in rows) / 60, 1))
