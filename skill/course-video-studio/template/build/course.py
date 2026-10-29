# -*- coding: utf-8 -*-
"""Single source of truth for the course: modules, lessons, paths. Every other script reads this.

Edit COURSE, PARTS and MODULES for your course. A lesson id is a short ASCII name (m1l1, m2l3, bonus1);
its script lives in videos/<id>/lesson.py. Lessons without a lesson.py are simply skipped by "all".
"""
import importlib.util
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parent
VIDEOS = BUILD / "videos"
ENGINE = BUILD / "engine"
COMMON = BUILD / "common"
OUT = ROOT / "סרטונים"

COURSE = {
    "title": "שם הקורס",
    "subtitle": "משפט אחד שמסביר מה מקבלים",
    "brand": "<b>שם הקורס</b>",          # shown small in the corner of every video
    "instructor": "שם המדריך",
}

# Levels (parts). One part is fine; the key "בונוס" gets a bonus label instead of a level name.
PARTS = {
    "א": {"name": "מתחילים", "tag": "התחלה קלה", "goal": "מה הלומד יודע לעשות בסוף הרמה הזאת"},
}

# Each lesson: (id, title, one-line promise). The promise appears on the title card, in the syllabus and in the guide.
MODULES = [
    {"n": 1, "part": "א", "name": "פרק הדוגמה", "dir": "01 - פרק ראשון", "lessons": [
        ("demo1", "שיעור לדוגמה", "איך נראה שיעור שנבנה במערכת הזאת"),
        ("demo2", "השיעור הבא", "כאן יבוא השיעור השני שלכם"),
    ]},
]

# Lessons that end the course (a goodbye instead of "בשיעור הבא").
FINAL_LESSONS = ("demo2",)

LESSONS = [(lid, title, promise, m) for m in MODULES for lid, title, promise in m["lessons"]]


def lesson_meta(lid):
    for k, (i, title, promise, m) in enumerate(LESSONS):
        if i == lid:
            nxt = LESSONS[k + 1][1] if k + 1 < len(LESSONS) else ""
            num = f'{m["n"]}.{m["lessons"].index((i, title, promise)) + 1}'
            if i in FINAL_LESSONS:
                nxt = ""
            return {"id": i, "title": title, "promise": promise, "module": m, "num": num, "next": nxt,
                    "part": m["part"], "part_name": PARTS[m["part"]]["name"]}
    raise SystemExit(f"unknown lesson {lid}")


def lesson_ids(args):
    if not args or args == ["all"]:
        return [l[0] for l in LESSONS if (VIDEOS / l[0] / "lesson.py").exists()]
    return args


def load_lesson(lid):
    if str(ENGINE) not in sys.path:
        sys.path.insert(0, str(ENGINE))
    path = VIDEOS / lid / "lesson.py"
    spec = importlib.util.spec_from_file_location(f"lesson_{lid}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
