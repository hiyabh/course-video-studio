# -*- coding: utf-8 -*-
"""Generate chapter sub-compositions from beat specs (beats/<id>.json, written by write_specs.py).
Usage: python beats.py [ch0 ch1 ...]
A beat starts at its anchor phrase (resolved in order from words.json) and ends at the next beat.
Sub-anchors: "reveal" (list of phrases) and "shots" (list of {"at", "focus", "zoom"})."""
import json
import sys

import beat_types_app
import beat_types_device
import beat_types_diagram
import beat_types_text
import beat_types_visual
import deco
import sfx
from anchor import find, stream
from captions_layer import captions_section
from config import BUILD, CLIP
from transitions import pick, transition

CHAPTERS = json.loads((BUILD / "chapters.json").read_text(encoding="utf-8"))
RENDER = {**beat_types_app.RENDER, **beat_types_device.RENDER, **beat_types_text.RENDER, **beat_types_visual.RENDER, **beat_types_diagram.RENDER}
LEAD = 0.15          # a beat appears this long after its anchor word starts
MIN_BEAT = 1.6       # shorter beats are a spec error (the static checker keeps 2.5 as authoring margin)
BEAT_TRACKS = (1, 4)
ERRORS = []
KINETIC_LATE = ("kinetic",)
LATE_GAP = 1.2
LATE_LEAD = 0.5


def _hit(words, phrase, after, ch, what):
    if isinstance(phrase, (int, float)):
        return float(phrase)
    hits = find(words, phrase, after - LEAD - 0.01)
    if not hits or hits[0] >= ch["end"]:
        ERRORS.append(f"{ch['id']}: {what} {phrase!r} not found after {after:.1f}")
        return None
    return hits[0] + LEAD


def resolve(words, beats, ch):
    """Set b['g'] (global start) and b['_reveal'] / b['_shots'] for every beat, monotonic in time."""
    cursor = ch["start"]
    for i, b in enumerate(beats):
        if i == 0:
            b["g"] = ch["start"]
        else:
            t = _hit(words, b["at"], cursor + LEAD, ch, f"beat {i} anchor")
            b["g"] = max(t if t is not None else cursor + MIN_BEAT * 2, cursor)
        cursor = b["g"]
        if b["t"] == "kinetic" and "reveal" not in b:
            b["reveal"] = b["words"]
        if "reveal" in b:
            b["_reveal"] = [x for x in (_hit(words, p, cursor, ch, "reveal") for p in b["reveal"]) if x is not None]
            # Kinetic words have nothing to show before their first word: start the beat just before it.
            if b["t"] in KINETIC_LATE and i > 0 and b["_reveal"] and b["_reveal"][0] - b["g"] > LATE_GAP:
                b["g"] = round(b["_reveal"][0] - LATE_LEAD, 2)
                cursor = b["g"]
        if b.get("shots"):
            b["_shots"] = [_hit(words, sh["at"], cursor, ch, "shot") or cursor + 4 for sh in b["shots"]]
    return beats


def _beat_html(cid, k, b, s, dur, chnum):
    bid = f"{cid}-b{k}"
    if b["t"] == "title":
        b = {**b, "_chnum": chnum + 1, "_chcount": len(CHAPTERS["chapters"]) if chnum >= 0 else 0}
    poster = chnum == 0 and k == 0   # frame 0 is the preview image in WhatsApp and course players
    if poster:
        b = {**b, "_poster": True}
    rel = [round(t - (b["g"] - s), 2) for t in b.get("_reveal", [])]
    shots = {**b, "_shots": [round(t - (b["g"] - s), 2) for t in b.get("_shots", [])]}
    inner, lines = RENDER[b["t"]](bid, shots, s, dur, rel, k)
    overlay, tr_js = transition(bid, pick(b["t"], k, b.get("tr")), s)
    n = chnum * 10 + k
    deco_html, deco_js = deco.shapes(bid, b["t"], n, s, dur)
    paper_html, paper_js = deco.paper(bid, b["t"], s)
    deco_html, deco_js = paper_html + deco_html, paper_js + deco_js
    if deco_html and inner.startswith("<div"):
        cut = inner.index(">") + 1
        inner = inner[:cut] + deco_html + inner[cut:]
    color = deco.PALETTE[0] if b["t"] in ("title", "closing") else deco.accent(n)
    section = (f'<section id="{bid}" class="clip beat t-{b["t"]}" style="--torah:{color}" data-start="{s}" data-duration="{dur}" '
               f'data-track-index="{BEAT_TRACKS[k % 2]}">{inner}{overlay}</section>')
    if not poster:
        sfx.ev("whoosh", max(0.0, s - 0.12))
        if b["t"] in ("title", "closing"):
            sfx.ev("chime", s + 0.25)
    if poster:
        fade = [f'tl.to(R.querySelector("#{bid} > .in"), {{ opacity: 0, duration: 0.4, ease: "power1.in" }}, {round(s + dur - 0.4, 2)});']
        return section, fade + lines + deco_js
    return section, [f'K.beat(tl, R, "{bid}", {s}, {dur});'] + tr_js + lines + deco_js


def build_chapter(chnum, ch, spec, words):
    beats = resolve(words, spec["beats"], ch)
    start, end, cid = ch["start"], ch["end"], ch["id"]
    sections, js = [], []
    mark = len(sfx.EVENTS)
    for k, b in enumerate(beats):
        s = round(b["g"] - start, 2)
        e = round((beats[k + 1]["g"] if k + 1 < len(beats) else end) - start, 2)
        if e - s < MIN_BEAT:
            ERRORS.append(f"{cid} beat {k} ({b['t']}) only {e - s:.2f}s at {b['g']:.1f} - merge or move anchors")
        html, lines = _beat_html(cid, k, b, s, round(e - s, 2), chnum)
        sections.append(html)
        js.extend(lines)
    for e in sfx.EVENTS[mark:]:
        e["t"] = round(e["t"] + start, 3)
    cap_html, cap_js = captions_section(cid, start, end, spec.get("keywords", []))
    return page(cid, round(end - start, 3), spec.get("ghost", ""), sections, js + cap_js, cap_html)


def page(cid, total, ghost, sections, js, cap_html):
    body = "\n        ".join(sections)
    script = "\n          ".join(js)
    return f"""<!doctype html>
<html>
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <style>
        #root {{ position: absolute; inset: 0; }}
      </style>
      <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080">
        <div id="{cid}-ghostwrap" class="clip" data-start="0" data-duration="{total}" data-track-index="0">
          <div id="{cid}-ghost" class="ghost">{ghost}</div>
        </div>
        {body}
        {cap_html}
      </div>
      <script>
        (function () {{
          const R = document.querySelector('[data-composition-id="{cid}"]');
          const tl = gsap.timeline({{ paused: true }});
          K.drift(tl, R, "#{cid}-ghost", 0, {total}, {{ x: 260 }});
          {script}
          window.__timelines["{cid}"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""


def load_spec(cid):
    path = BUILD / "beats" / f"{cid}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main(ids):
    words = stream()
    for chnum, ch in enumerate(CHAPTERS["chapters"]):
        spec = load_spec(ch["id"])
        if (ids and ch["id"] not in ids) or not spec:
            continue
        html = build_chapter(chnum, ch, spec, words)
        (CLIP / "compositions" / f"{ch['id']}.html").write_text(html, encoding="utf-8")
        print(f"{ch['id']}: {len(spec['beats'])} beats")
    if not ids:
        sfx.save(BUILD / "sfx.json")
    print(chr(10).join(ERRORS) or "all anchors resolved")
    sys.exit(1 if ERRORS else 0)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
