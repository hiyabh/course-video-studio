# Writing guide - one lesson = one file `build/videos/<id>/lesson.py`

You write the narration AND the animation plan of one course lesson. The audience and tone come from the
course owner (ask once, then record them at the top of `build/FACTS.md` or in the project's CLAUDE.md).
Default bar: the clearest Hebrew online course the learner ever bought. Warm, practical, zero jargon.

Read first: `build/FACTS.md` (the ONLY source for prices, dates, names, button labels), `build/course.py`
(your lesson's title + promise and the next lesson), `build/videos/demo1/lesson.py` (a finished example),
`build/engine/spec_helpers.py` (beat constructors). Then write, then run the checker until it passes:

    python -X utf8 check_lesson.py <id>        (from inside build/)

## Narration (BLOCKS)
- 380-470 words per lesson (~3-3.7 minutes at the TTS pace of ~126 words per minute). 6-9 blocks of 40-80 words.
  The checker warns outside 330-520 and fails below 200 or above 600 (`WORDS_RANGE` in check_lesson.py).
- The narrator is the instructor speaking to the learners in plural ("אתם", "תפתחו", "שימו לב").
  Short sentences. One idea per sentence. Explain every term the first time it appears.
- Teach by doing: most lessons show one concrete example the learner can copy.
- One everyday analogy per lesson is plenty (a new employee, a recipe, a room, an architect's plan).
- Lesson shape (adapt freely): hook -> the idea -> demo -> how-to steps -> a tip or common mistake ->
  "נסו בעצמכם" -> one-sentence recap -> teaser.
- The LAST block starts with "בשיעור הבא" and names the next lesson's topic (course.py order).
  Lessons listed in `FINAL_LESSONS` end with a goodbye instead.
- The text is read by a TTS engine, therefore:
  - NO em/en dashes, slash, parentheses, asterisks, quotation marks of any kind, %, #, &, arrows (the checker fails on them).
    Write "אחוז", "או", commas. For a quoted request: למשל, כתבו לו: תסדר לי את התיקייה לפי חגים.
  - No niqqud and no abbreviations ("למשל", not "לדוג'"). Numbers as digits are fine (20 דולר, 3 דקות).
  - English words only when the learner must find them on screen, never more than ~4 per block.
    Start every block with a Hebrew word. Never glue a Hebrew prefix to an English word (ו-Claude, ב-Word):
    the RTL caption flips it. Rephrase instead (והעוזר, בקובץ וורד).
  - Pronunciation fix: `{display|spoken}` shows `display` in the captions and sends `spoken` to the TTS,
    for example `{ו׳|וָו}` or `{Git|גִּיט}`. Add English words the transcriber must recognise to `TRANSLIT` in narrate.py.
- Never tell learners to copy text from the video. Say: כתבו את הבקשה שעל המסך, או העתיקו אותה מהמדריך המלווה.
  The companion guide collects every PROMPT beat automatically.
- Facts ONLY from FACTS.md. If unsure, do not say it. Never invent statistics, quotes or features.

## Animation (CHAPTERS)
3-5 chapters. Each chapter: `{"id": "ch0".., "title": short label shown top-right, "ink": "warm|torah|math|both",
"at": 0 for ch0 else an anchor phrase, "ghost": 1-2 big background words, "beats": [...]}`.
- FIRST beat of the lesson: `LT("שיעור <num>", "<title>", "<promise>", eyebrow=...)`. The build syncs badge,
  title, promise and eyebrow from course.py, so moving a lesson never needs a lesson.py edit.
- LAST beat: `END("בשיעור הבא", "<next lesson title>", "בשיעור הבא", "<one short line>")` (the checker warns on a mismatch).
- An anchor (`at`, `reveal`, chapter `at`) is 1-4 CONSECUTIVE words copied exactly from the narration
  (punctuation ignored). Anchors resolve in order, each after the previous beat; prefer 2-3 word phrases
  that appear once. A beat lasts until the next one (min 2.5s).
- Something must move at least every 12 seconds: a new beat or a reveal inside a beat. Aim for a beat every 8-12s.
- Max ~6 short items in a list, titles up to 5 words, chip and node text 1-4 words. STEPS: at most 4 cards
  (5 overflow the screen).

| Beat | Use |
|---|---|
| `SAY(at, "line with *highlight*")`, `Q(at, "question?", sub)` | punchline, question |
| `KW(at, big, [chips], reveal=[..])`, `KIN(at, [2-4 words], reveal=[..])` | key words, kinetic type |
| `L(at, title, items, reveal=[..])` | list |
| `C(at, right_head, [lines], left_head, [lines], mid="מול", reveal=[left_at])` | compare, right side first |
| `STEPS(at, [{"icon": emoji, "h": "..", "d": ".."}], title=, reveal=[..])` | 2-4 numbered steps |
| `N(at, number, label, sub, suffix="")` | a number that counts up |
| `FLOW`, `CYCLE`, `LADDER`, `STACK`, `SCALE`, `VENN`, `TL`, `BARS` | live diagrams (see spec_helpers.py) |
| `S(at, "img", cap, sub)`, `IT(at, "img", title, [lines], reveal)`, `SPLIT(at, "img", quote, cite)` | illustrations from common/img |
| `SHOT(at, "file.png", url=, marks=[{"box": [x%, y%, w%, h%], "label": "..", "zoom": 1.6}], reveal=[..])` | a real screenshot from common/shots with highlight boxes |
| `PROMPT(at, "request text", title="נסו בעצמכם", note="...")` | an exercise or request card, at least one per lesson |
| `LINK(at, "title", "https://...", sub=, icon=)` | a link card with a QR code. Never read the address aloud |
| `FILES(at, files=[..], folders=[{"name", "items": [indices]}], title=, reveal=[..])` | messy files fly into folders |
| `APP(at, [you(..), tool(..), ask(..), say(..), done(..), file(..)], folder=, mode=, hi=[..], reveal=[..])` | an animated Claude Code desktop window, for software-demo lessons. Up to 6 steps |
| `PHONE(at, steps, title=, reveal=)` | a phone mockup with a chat |
| `V(at, pasuk, cite)`, `SRC(at, quote, cite)` | a verse with niqqud (verify it against Sefaria first) or a sourced quote |

## Media
- Illustrations: `build/common/img/<name>.png`, 1920x1080. New ones: add a scene to `SCENES` in gen_images.py
  and run `python -X utf8 gen_images.py <name>`; check `qc_images.jpg` before using them. Use each image once
  or twice in the whole course, 1-2 per lesson.
- Screenshots: `build/common/shots/<file>.png`. Measure mark boxes as percentages of the real image and
  check them with `python -X utf8 qc_marks.py <id>` before rendering. Portrait images look small; use
  them only when the point is "look, a real document".
- People in generated images: modest dress, a married woman wears only a tichel tied behind the head with
  face, chin and neck visible; never a hijab, veil or hood. Characters in a negative or embarrassing role are
  never identifiably Jewish (no kippah, no tzitzit). Zoom into small background figures before approving.

## Done
The checker prints "ALL LESSONS OK", and after narration both sync checks are clean. Read the narration once
aloud in your head: would a learner who never saw the topic follow every sentence? If not, simplify.
