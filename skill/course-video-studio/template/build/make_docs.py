# -*- coding: utf-8 -*-
"""Course documents from the syllabus + the lesson files: syllabus, platform upload texts, companion guide.

    python -X utf8 make_docs.py        -> 00/01/02 MD + DOCX in the course root (+ PDF of the guide)
"""
import shutil
import subprocess
import sys
from pathlib import Path

from course import COURSE, LESSONS, MODULES, PARTS, ROOT, VIDEOS, lesson_meta, load_lesson
import doc_content as dc
import md2docx

DOCS = {
    "syllabus": "00 - סילבוס הקורס",
    "upload": "01 - טקסטים לדף הקורס",
    "guide": "02 - מדריך מלווה",
}
SOFFICE_PATHS = ("C:/Program Files/LibreOffice/program/soffice.exe", "/Applications/LibreOffice.app/Contents/MacOS/soffice")


def minutes(lid):
    audio = VIDEOS / lid / "clip" / "assets" / "audio" / "lesson.m4a"
    if not audio.exists():
        return None
    out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)],
                         capture_output=True, text=True).stdout.strip()
    return float(out) / 60 if out else None


def fmt(m):
    if m is None:
        return "כ-3 דק'"
    s = round(m * 60)
    return f"{s // 60}:{s % 60:02d}"


def total_minutes():
    ms = [minutes(l[0]) for l in LESSONS]
    known = [m for m in ms if m]
    return round(sum(known)), len(known)


def beats_of(lid):
    try:
        les = load_lesson(lid)
    except FileNotFoundError:
        return []
    return [b for c in les.CHAPTERS for b in c["beats"]]


def key_points(lid):
    pts = []
    for b in beats_of(lid):
        if b["t"] == "steps":
            pts += [f'{s["h"]}: {s["d"]}' if s.get("d") else s["h"] for s in b["steps"]]
        elif b["t"] == "list":
            pts += b["items"]
        elif b["t"] == "say":
            pts.append(b["text"].replace("*", ""))
    seen, out = set(), []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:8]


def prompts(lid):
    return [b["text"] for b in beats_of(lid) if b["t"] == "prompt"]


def module_table(m):
    rows = ["| מספר | שיעור | מה לומדים | משך |", "|---|---|---|---|"]
    for lid, title, promise in m["lessons"]:
        rows.append(f'| {lesson_meta(lid)["num"]} | {title} | {promise} | {fmt(minutes(lid))} |')
    return "\n".join(rows)


def num(lid):
    return lesson_meta(lid)["num"]


def part_heading(key, level="##"):
    p = PARTS[key]
    head = f"{level} בונוס: {p['tag']}" if key == "בונוס" else f"{level} רמת {p['name']}: {p['tag']}"
    return [head, "", p["goal"]]


def modules_of(key):
    return [m for m in MODULES if m["part"] == key]


def syllabus():
    tot, n = total_minutes()
    parts = [f'# סילבוס הקורס - {COURSE["title"]}', "",
             f'**{COURSE["subtitle"]}**', "",
             f'{len(LESSONS)} שיעורי וידאו קצרים · {len(MODULES)} פרקים · כ-{tot} דקות צפייה · מדריך מלווה עם ספריית בקשות', "",
             "## על הקורס", dc.ABOUT, "",
             "## למי הקורס מיועד", *[f"- {a}" for a in dc.AUDIENCE], "",
             "## מה תדעו לעשות בסוף הקורס", *[f"{k}. {o}" for k, o in enumerate(dc.OUTCOMES, 1)], "",
             "## מה צריך כדי להתחיל", *[f"- {r}" for r in dc.REQUIREMENTS], "",
             "## מבנה הקורס"]
    for key in PARTS:
        if len(PARTS) > 1:
            parts += [""] + part_heading(key)
        for m in modules_of(key):
            parts += ["", f'### פרק {m["n"]}: {m["name"]}', "", module_table(m)]
    parts += ["", "## איך ללמוד את הקורס",
              "- כל שיעור עוסק בנושא אחד. מומלץ ללמוד בסדר, כי כל שיעור נשען על הקודם.",
              "- כל הבקשות והתרגילים מהקורס מרוכזים במדריך המלווה.",
              "- בכל סרטון יש כתוביות בעברית שצרובות בתמונה, והמילה הנאמרת מודגשת."]
    if dc.LINKS:
        parts += ["", "## קישורים", *dc.links_md()]
    return "\n".join(parts)


def upload():
    tot, _ = total_minutes()
    parts = [f'# טקסטים לדף הקורס - {COURSE["title"]}', "",
             "## שם הקורס", COURSE["title"], "",
             "## כותרת משנה", COURSE["subtitle"], "",
             "## תיאור", dc.ABOUT, "",
             "## למי זה מתאים", *[f"- {a}" for a in dc.AUDIENCE], "",
             "## מה בפנים",
             f"- {len(LESSONS)} שיעורי וידאו ב-{len(MODULES)} פרקים, כ-{tot} דקות",
             "- כתוביות בעברית צרובות בכל שיעור",
             "- מדריך מלווה עם עיקרי כל שיעור", ""]
    if dc.FAQ:
        parts += ["## שאלות נפוצות", *dc.faq_md(num), ""]
    parts += ["## תיאור לכל שיעור"]
    for m in MODULES:
        parts += ["", f'#### פרק {m["n"]}: {m["name"]}']
        for lid, title, promise in m["lessons"]:
            parts += ["", f'**{num(lid)} {title}** - {promise}']
    parts += ["", "## הגדרות העלאה",
              "- קובצי הווידאו: MP4 בפורמט H.264, ברזולוציה 1920 על 1080, עם שמע AAC.",
              "- הכתוביות צרובות בתוך הסרטון, ולכן אין צורך להעלות קובץ כתוביות נפרד.",
              "- לכל שיעור יש תמונה ממוזערת JPG באותו שם."]
    return "\n".join(parts)


def guide():
    parts = [f'# מדריך מלווה - {COURSE["title"]}', "",
             "המדריך מרכז את עיקרי כל שיעור ואת כל הבקשות והתרגילים שהופיעו בקורס, מוכנים להעתקה.", ""]
    if dc.LINKS:
        parts += ["## קישורים חשובים", *dc.links_md(), ""]
    for key in PARTS:
        if len(PARTS) > 1:
            parts += [""] + part_heading(key)
        for m in modules_of(key):
            parts += guide_module(m)
        if dc.PART_QUESTIONS.get(key):
            parts += ["", f"### שאלות סיום לרמת {PARTS[key]['name']}", "",
                      "לפני שממשיכים, נסו לענות בלי להציץ. אם שאלה אחת מתעכבת, חזרו לשיעור המתאים.", ""]
            parts += [f"{k}. {q_}" for k, q_ in enumerate(dc.PART_QUESTIONS[key], 1)]
    if dc.GOLDEN:
        parts += ["", "## כללי הזהב", *[f"{k}. {g}" for k, g in enumerate(dc.GOLDEN, 1)]]
    if dc.FAQ:
        parts += ["", "## שאלות נפוצות", "", *dc.faq_md(num)]
    return "\n".join(parts)


def guide_module(m):
    parts = ["", f'### פרק {m["n"]}: {m["name"]}']
    for lid, title, promise in m["lessons"]:
        parts += ["", f'#### {num(lid)} {title}', "", f"*{promise}*", ""]
        parts += [f"- {p}" for p in key_points(lid)]
        pr = prompts(lid)
        if pr:
            parts += ["", "**לנסות בעצמכם:**", ""]
            parts += [f"- {p}" for p in pr]
    return parts


def soffice():
    found = shutil.which("soffice") or next((p for p in SOFFICE_PATHS if Path(p).exists()), None)
    if not found:
        print("pdf: LibreOffice not found - install it, or open the guide DOCX in Word and save as PDF")
    return found


def main():
    for key, fn in (("syllabus", syllabus), ("upload", upload), ("guide", guide)):
        md = ROOT / f"{DOCS[key]}.md"
        md.write_text(fn(), encoding="utf-8")
        md2docx.main(str(md), str(ROOT / f"{DOCS[key]}.docx"))
    if "--pdf" in sys.argv and soffice():
        subprocess.run([soffice(), "--headless", "--convert-to", "pdf", "--outdir", str(ROOT), str(ROOT / f'{DOCS["guide"]}.docx')],
                       capture_output=True)
        print("pdf:", (ROOT / f'{DOCS["guide"]}.pdf').exists())


if __name__ == "__main__":
    main()
