# -*- coding: utf-8 -*-
"""Resolve every beat/reveal anchor against the REAL narration timing (words.json) and flag
reveals that fire out of order inside a beat (e.g. a demo answer before the request)."""
import json, sys
sys.path.insert(0, "."); sys.path.insert(0, "engine")
from course import LESSONS, VIDEOS, load_lesson, lesson_meta
from anchor import norm, find
LEAD = 0.15
def words_of(lid):
    segs = json.load(open(VIDEOS / lid / "build" / "words.json", encoding="utf-8"))
    out = []
    for s in segs:
        for w in s["words"]:
            n = norm(w["w"])
            if n: out.append((n, w["s"]))
    return out
def hit(words, p, after):
    h = find(words, p, after - LEAD - 0.01); return h[0] if h else None
issues = 0
for lid, _, _, _ in LESSONS:
    if not (VIDEOS / lid / "build" / "words.json").exists():  # not written or not narrated yet
        continue
    les = load_lesson(lid); words = words_of(lid); meta = lesson_meta(lid)
    cursor = 0.0; starts = []
    for ch in les.CHAPTERS:
        t = 0.0 if ch["at"] == 0 else hit(words, ch["at"], cursor)
        starts.append(t); cursor = t
    for ci, ch in enumerate(les.CHAPTERS):
        cur = starts[ci]
        for bi, b in enumerate(ch["beats"]):
            g = cur if bi == 0 else (hit(words, b["at"], cur + LEAD) or cur)
            g = max(g, cur); cur = g
            rev = b.get("reveal", b.get("words", []) if b["t"] == "kinetic" else [])
            times = [hit(words, p, g) for p in rev]
            if b["t"] == "app":
                n = len(b["steps"]); st = [t for t in times[:n] if t is not None]
                bad = [(k, rev[k], round(st[k]-g,1)) for k in range(1, len(st)) if st[k] < st[k-1]]
                if bad:
                    issues += 1; print(f"[{lid} {meta['num']}] {ch['id']} beat{bi} APP steps out of order: {bad}  all={[round(t-g,1) if t else None for t in times]}")
                for j, hh in enumerate(b.get("hi", [])):
                    k = n + j
                    if k >= len(rev):
                        print(f"[{lid} {meta['num']}] {ch['id']} beat{bi} APP hi '{hh['el']}' auto-timed (after last step)")
            else:
                tt = [t for t in times if t is not None]
                bad = [(k, rev[k], round(tt[k]-g,1), round(tt[k-1]-g,1)) for k in range(1, len(tt)) if tt[k] < tt[k-1]]
                if bad:
                    issues += 1; print(f"[{lid} {meta['num']}] {ch['id']} beat{bi} {b['t']} reveals out of order: {bad}")
            if b["t"] == "shot":
                mk = b.get("marks", [])
                if len(mk) > 1 and len(rev) >= 2:
                    pass
print("issues:", issues)
