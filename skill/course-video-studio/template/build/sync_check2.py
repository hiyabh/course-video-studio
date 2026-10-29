# -*- coding: utf-8 -*-
"""Flag reveals/steps/rings that resolve AFTER their beat has already ended (next beat started)."""
import json, sys
sys.path.insert(0, "."); sys.path.insert(0, "engine")
from course import LESSONS, VIDEOS, load_lesson, lesson_meta
from anchor import norm, find
LEAD = 0.15
def words_of(lid):
    segs = json.load(open(VIDEOS / lid / "build" / "words.json", encoding="utf-8"))
    return [(norm(w["w"]), w["s"]) for s in segs for w in s["words"] if norm(w["w"])]
def hit(words, p, after):
    h = find(words, p, after - LEAD - 0.01); return h[0] if h else None
n_issues = 0
for lid, _, _, _ in LESSONS:
    if not (VIDEOS / lid / "build" / "words.json").exists():  # not written or not narrated yet
        continue
    les = load_lesson(lid); words = words_of(lid); meta = lesson_meta(lid)
    total = words[-1][1] + 3
    cursor = 0.0; starts = []
    for ch in les.CHAPTERS:
        t = 0.0 if ch["at"] == 0 else hit(words, ch["at"], cursor); starts.append(t); cursor = t
    for ci, ch in enumerate(les.CHAPTERS):
        ch_end = starts[ci + 1] if ci + 1 < len(starts) else total
        cur = starts[ci]; gs = []
        for bi, b in enumerate(ch["beats"]):
            g = cur if bi == 0 else (hit(words, b["at"], cur + LEAD) or cur)
            g = max(g, cur); cur = g; gs.append(g)
        for bi, b in enumerate(ch["beats"]):
            g = gs[bi]; end = gs[bi + 1] if bi + 1 < len(gs) else ch_end
            rev = b.get("reveal", b.get("words", []) if b["t"] == "kinetic" else [])
            late = []
            for k, p in enumerate(rev):
                t = hit(words, p, g)
                if t is not None and t > end - 0.4:
                    what = "step" if (b["t"] == "app" and k < len(b["steps"])) else ("ring" if b["t"] == "app" else "reveal")
                    late.append(f"{what}{k} '{p}' at +{t-g:.1f}s but beat ends at +{end-g:.1f}s")
            if late:
                n_issues += 1
                print(f"[{lid} {meta['num']}] {ch['id']} beat{bi} {b['t']} ({str(b.get('at'))[:20]!r}): " + "; ".join(late))
print("issues:", n_issues)
