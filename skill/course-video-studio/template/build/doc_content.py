# -*- coding: utf-8 -*-
"""Hand-written document content that does not come from the lessons: about, audience, links, FAQ, questions.
Fill it for your course; make_docs.py builds the syllabus, the upload texts and the companion guide from it.
Every fact here (prices, dates, names) must also appear in FACTS.md with its source."""

ABOUT = "פסקה אחת: מה הקורס מלמד, למי, ובאיזו דרך."

AUDIENCE = [
    "קהל יעד ראשון",
    "קהל יעד שני",
]

REQUIREMENTS = [
    "מה צריך כדי להתחיל, למשל מחשב וחיבור לאינטרנט",
]

OUTCOMES = [
    "דבר ראשון שהלומד יודע לעשות בסוף הקורס",
    "דבר שני",
]

# (name, url, note). Leave empty if there is nothing to link.
LINKS = []

# (question, answer). {lesson_id} inside an answer becomes that lesson's number, e.g. "ראו שיעור {demo1}".
FAQ = [
    ("צריך ידע קודם?", "לא. הקורס מתחיל מאפס. ראו שיעור {demo1}."),
]

# Self-check questions at the end of each level (keyed by PARTS key in course.py).
PART_QUESTIONS = {
    "א": [
        "שאלה שבודקת שהבנתם את הרמה הראשונה",
    ],
}

# Short rules that close the companion guide. Leave empty to skip the section.
GOLDEN = []


def links_md():
    return [f"- **{name}:** {url} - {note}" for name, url, note in LINKS]


def faq_md(num):
    """num(lesson_id) -> lesson number, so references never go stale when lessons move."""
    import re
    out = []
    for q, a in FAQ:
        out += [f"**{q}** " + re.sub(r"\{(\w+)\}", lambda m: num(m.group(1)), a), ""]
    return out[:-1]
