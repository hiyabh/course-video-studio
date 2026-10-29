# -*- coding: utf-8 -*-
"""Re-transcribe the delivered narration of every lesson and diff it against the script.
Output: qc/transcribe/<id>.json + qc/transcribe_report.md"""
import difflib, json, sys
from pathlib import Path
sys.path.insert(0, ".")
from course import LESSONS, VIDEOS, load_lesson, lesson_meta
import narrate
from faster_whisper import WhisperModel

OUTD = Path("qc/transcribe"); OUTD.mkdir(parents=True, exist_ok=True)
model = WhisperModel(narrate.WHISPER, device="cpu", compute_type="int8", cpu_threads=8)
ids = sys.argv[1:] or [l[0] for l in LESSONS if (VIDEOS / l[0] / "clip" / "assets" / "audio" / "lesson.m4a").exists()]
report = ["# דוח תמלול מול תסריט", ""]
for lid in ids:
    out = OUTD / f"{lid}.json"
    audio = VIDEOS / lid / "clip" / "assets" / "audio" / "lesson.m4a"
    if out.exists() and out.stat().st_mtime > audio.stat().st_mtime:  # re-narrated audio must be re-heard
        d = json.loads(out.read_text(encoding="utf-8"))
    else:
        les = load_lesson(lid)
        segs, _ = model.transcribe(str(audio), language="he", word_timestamps=True, condition_on_previous_text=False, beam_size=5)
        heard = [{"w": w.word.strip(), "s": round(w.start, 2)} for s in segs for w in s.words if w.word.strip()]
        spk = []
        for b in les.BLOCKS:
            for _, s in narrate.units(b):
                spk += s
        ek = [narrate.key(w) for w in spk]
        hk = [narrate.key(h["w"]) for h in heard]
        sm = difflib.SequenceMatcher(None, ek, hk, autojunk=False)
        diffs = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            diffs.append({"op": op, "t": heard[j1]["s"] if j1 < len(heard) else heard[-1]["s"],
                          "script": " ".join(spk[i1:i2]), "heard": " ".join(h["w"] for h in heard[j1:j2]),
                          "ctx": " ".join(spk[max(0, i1 - 3):i1])})
        d = {"id": lid, "ratio": round(sm.ratio(), 3), "n_script": len(ek), "n_heard": len(hk), "diffs": diffs,
             "heard_text": " ".join(h["w"] for h in heard)}
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    m = lesson_meta(lid)
    print(f"[{lid}] {m['num']} ratio={d['ratio']} diffs={len(d['diffs'])}", flush=True)
    report.append(f"## {m['num']} {m['title']} ({lid}) - ratio {d['ratio']}, {len(d['diffs'])} הבדלים")
    for x in d["diffs"]:
        report.append(f"- {x['t']:.0f}s {x['op']}: תסריט «{x['script']}» | נשמע «{x['heard']}» (אחרי: {x['ctx']})")
    report.append("")
Path("qc/transcribe_report.md").write_text("\n".join(report), encoding="utf-8")
print("DONE")
