# -*- coding: utf-8 -*-
"""Local preview page of the whole course: 'צפייה בקורס.html' in the course root (videos play from disk).

    python -X utf8 make_preview.py
"""
import html
from urllib.parse import quote

from course import COURSE, MODULES, PARTS, ROOT, lesson_meta
from make_docs import fmt, minutes
from render_video import out_paths

OUT = ROOT / "צפייה בקורס.html"
CSS = """
:root{--bg:#11131B;--card:#1C1F2B;--fg:#F5F0E8;--muted:#A7ACBD;--acc:#EE9A70}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:Assistant,Rubik,Arial,sans-serif}
header{padding:48px 16px 24px;text-align:center}h1{margin:0;font:700 clamp(36px,6vw,64px)/1.1 Rubik,Arial;color:var(--acc)}
header p{color:var(--muted);font-size:20px;margin:12px 0 0}
main{max-width:1200px;margin:0 auto;padding:0 16px 64px}
h2{font:700 28px Rubik,Arial;margin:40px 0 16px;border-inline-start:6px solid var(--acc);padding-inline-start:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px}
.card{background:var(--card);border-radius:16px;overflow:hidden}
video{width:100%;display:block;background:#000;aspect-ratio:16/9}
.meta{padding:14px 18px}.meta b{font-size:20px}.meta div{color:var(--muted);margin-top:4px}
.dur{float:left;color:var(--acc);font-weight:700}.missing{padding:40px;text-align:center;color:var(--muted)}
h1.part{font-size:clamp(28px,4vw,40px);margin:64px 0 4px;color:var(--fg)}.goal{color:var(--muted);margin:0 0 8px;font-size:18px}
"""


def rel(p):
    return quote(p.relative_to(ROOT).as_posix())


def card(lid):
    meta = lesson_meta(lid)
    mp4, jpg = out_paths(lid)
    if mp4.exists():
        media = (f'<video controls preload="none" poster="{rel(jpg)}"><source src="{rel(mp4)}" type="video/mp4">'
                 f'</video>')
    else:
        media = '<div class="missing">הסרטון עדיין לא נוצר</div>'
    return (f'<div class="card">{media}<div class="meta"><span class="dur">{fmt(minutes(lid))}</span>'
            f'<b>{meta["num"]} {html.escape(meta["title"])}</b><div>{html.escape(meta["promise"])}</div></div></div>')


def main():
    sections = ""
    for key, part in PARTS.items():
        head = "בונוס" if key == "בונוס" else f'רמת {part["name"]}: {part["tag"]}'
        sections += f'<h1 class="part">{html.escape(head)}</h1><p class="goal">{html.escape(part["goal"])}</p>'
        sections += "".join(
            f'<h2>פרק {m["n"]}: {html.escape(m["name"])}</h2><div class="grid">'
            + "".join(card(lid) for lid, _, _ in m["lessons"]) + "</div>" for m in MODULES if m["part"] == key)
    page = (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>{html.escape(COURSE["title"])}</title><style>{CSS}</style>'
            f'</head><body><header><h1>{html.escape(COURSE["title"])}</h1><p>{html.escape(COURSE["subtitle"])}</p></header>'
            f'<main>{sections}</main></body></html>')
    OUT.write_text(page, encoding="utf-8")
    print("preview:", OUT)


if __name__ == "__main__":
    main()
