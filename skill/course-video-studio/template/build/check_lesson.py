# -*- coding: utf-8 -*-
"""Static check of a lesson.py BEFORE narration (no audio needed).

    python -X utf8 check_lesson.py m2l3 [...|all]

Simulates narration timing (~0.47s per word), then checks: every chapter/beat/reveal anchor is found in
order, no beat shorter than 2.5s, no still stretch over 12s, word count, forbidden characters, blocks
start with a Hebrew word, the last block starts with "בשיעור הבא" (except the final lesson), media exists.
Exit code 1 on any error. Warnings do not fail.
"""
import os
import re
import sys

from course import COMMON, ENGINE, FINAL_LESSONS, lesson_ids, lesson_meta, load_lesson

os.environ.setdefault("VID", ".")
sys.path.insert(0, str(ENGINE))
import anchor  # noqa: E402  (engine on sys.path after load_lesson)

SEC_PER_WORD = 0.47
LEAD, GAP = 1.4, 0.5
BEAT_LEAD = 0.15
MIN_BEAT = 2.5
MAX_GAP = 12.0
WORDS_RANGE = (330, 520)
FORBIDDEN = {"—": "em dash", "–": "en dash", "/": "slash", "→": "arrow", "&": "ampersand", "\"": "straight double quote",
             "״": "gershayim", "(": "parenthesis", ")": "parenthesis", "*": "asterisk", "#": "hash", "%": "percent sign"}
MARKUP = re.compile(r"\{([^|{}]+)\|([^|{}]+)\}")
HEB_START = re.compile(r"^[א-ת]")
IMG_BEATS = ("story", "imgtext", "split")
STORY_EVERY = 6


def stream_of(blocks):
    words, t = [], LEAD
    for k, b in enumerate(blocks):
        disp = MARKUP.sub(lambda m: m.group(1), b).split()
        for w in disp:
            n = anchor.norm(w)
            if n:
                words.append((n, round(t, 2)))
            t += SEC_PER_WORD
        t += GAP
    return words, t


def hit(words, phrase, after):
    if isinstance(phrase, (int, float)):
        return float(phrase)
    h = anchor.find(words, phrase, after)
    return h[0] if h else None


def check(lid):
    les, meta = load_lesson(lid), lesson_meta(lid)
    errs, warns = [], []
    blocks = les.BLOCKS
    text = " ".join(blocks)
    n_words = len(MARKUP.sub(lambda m: m.group(1), text).split())
    if not WORDS_RANGE[0] <= n_words <= WORDS_RANGE[1]:
        (errs if n_words < 200 or n_words > 600 else warns).append(f"{n_words} words (target {WORDS_RANGE})")
    for ch, name in FORBIDDEN.items():
        if ch in MARKUP.sub("", text):
            errs.append(f"forbidden {name} {ch!r} in narration")
    for k, b in enumerate(blocks):
        if not HEB_START.match(b.strip()):
            warns.append(f"block {k + 1} does not start with a Hebrew word: {b[:30]!r}")
    is_last = lid in FINAL_LESSONS
    if not is_last and not blocks[-1].startswith("בשיעור הבא"):
        errs.append('last block must start with "בשיעור הבא"')
    end_beat = les.CHAPTERS[-1]["beats"][-1]
    if not is_last and end_beat.get("title") != meta["next"]:
        warns.append(f'END title {end_beat.get("title")!r} is not the next lesson {meta["next"]!r}')
    words, total = stream_of(blocks)
    cursor, events = 0.0, []
    chapters = les.CHAPTERS
    first = chapters[0]["beats"][0]
    if first["t"] != "title" or not first.get("badge"):
        errs.append("the first beat must be LT(...)")
    starts = []
    for c in chapters:
        t = hit(words, c.get("at", 0), cursor)
        if t is None:
            errs.append(f'{c["id"]}: chapter anchor {c["at"]!r} not found')
            t = cursor
        starts.append(t)
        cursor = t
    for ci, c in enumerate(chapters):
        end = starts[ci + 1] if ci + 1 < len(starts) else total
        cur = starts[ci]
        resolved = []
        for bi, b in enumerate(c["beats"]):
            if bi == 0:
                g = starts[ci]
            else:
                h = hit(words, b["at"], cur + BEAT_LEAD)
                if h is None or h >= end:
                    errs.append(f'{c["id"]} beat {bi} ({b["t"]}): anchor {b["at"]!r} not found inside the chapter')
                    h = cur + MIN_BEAT * 2
                g = max(h + BEAT_LEAD, cur)
            resolved.append((g, b))
            cur = g
            for p in b.get("reveal", b.get("words", []) if b["t"] == "kinetic" else []):
                r = hit(words, p, g - 0.2)
                if r is None or r >= end:
                    errs.append(f'{c["id"]} beat {bi} ({b["t"]}): reveal {p!r} not found after the beat starts')
                else:
                    events.append(r)
            for sh in b.get("shots") or []:
                r = hit(words, sh["at"], g)
                if r is None:
                    errs.append(f'{c["id"]} beat {bi}: shot {sh["at"]!r} not found')
                else:
                    events.append(r)
            if b["t"] in IMG_BEATS and not (COMMON / "img" / f'{b["img"]}.png').exists():
                errs.append(f'{c["id"]} beat {bi}: image {b["img"]!r} not in common/img')
            if b["t"] == "shot" and not (COMMON / "shots" / b["img"]).exists():
                errs.append(f'{c["id"]} beat {bi}: screenshot {b["img"]!r} not in common/shots')
            if b["t"] == "app":
                n_need = len(b["steps"]) + len(b.get("hi", []))
                if len(b.get("reveal", [])) < len(b["steps"]):
                    warns.append(f'{c["id"]} beat {bi}: app has {len(b["steps"])} steps but {len(b.get("reveal", []))} reveals')
                if len(b.get("reveal", [])) > n_need:
                    errs.append(f'{c["id"]} beat {bi}: more reveals than steps+highlights')
        for k, (g, b) in enumerate(resolved):
            e = resolved[k + 1][0] if k + 1 < len(resolved) else end
            if e - g < MIN_BEAT:
                errs.append(f'{c["id"]} beat {k} ({b["t"]}) only {e - g:.1f}s long')
            events.append(g)
            if b["t"] == "story" and e - g > 11:
                events += [g + STORY_EVERY * j for j in range(1, int((e - g) // STORY_EVERY))]
    if chapters[-1]["beats"][-1]["t"] != "closing":
        errs.append("the last beat must be END(...)")
    ev = sorted(events) + [total]
    for a, b in zip(ev, ev[1:]):
        if b - a > MAX_GAP:
            idx = [w for w, t in words if a <= t < b]
            errs.append(f"still {b - a:.1f}s at ~{a:.0f}s: '{' '.join(idx[:14])}...' - add a beat or reveal")
    print(f"[{lid}] {meta['num']} {meta['title']}: {n_words} words, ~{total / 60:.1f} min, "
          f"{sum(len(c['beats']) for c in chapters)} beats, {len(errs)} errors, {len(warns)} warnings")
    for e in errs:
        print(f"   ERROR {e}")
    for w in warns:
        print(f"   warn  {w}")
    return not errs


def main():
    ok = [check(lid) for lid in lesson_ids(sys.argv[1:])]
    print("ALL LESSONS OK" if all(ok) else "LESSONS HAVE ERRORS")
    sys.exit(0 if all(ok) else 1)


if __name__ == "__main__":
    main()
