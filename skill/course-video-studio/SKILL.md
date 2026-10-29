---
name: course-video-studio
description: >-
  Build a complete Hebrew video course from scratch: a syllabus in levels and chapters, then 2-4 minute
  animated lessons, each written as one text file (narration + scenes) and turned into a 1920x1080 MP4 with
  an AI narrator (Gemini TTS, checked by Whisper), scenes that land on the exact spoken words (titles, lists,
  comparisons, live diagrams, illustrations, screenshots with highlight boxes, exercise cards, QR links),
  burned-in karaoke captions and a thumbnail. Also produces a syllabus, upload texts and a companion guide
  (DOCX + PDF), a local preview page and a viewing-notes form. Fixing a sentence re-records only that paragraph.
  TRIGGER on Hebrew: 'תבנה לי קורס', 'קורס וידאו', 'קורס דיגיטלי', 'סרטוני קורס', 'שיעורים מונפשים לקורס',
  'קורס מונפש', 'סילבוס וסרטונים', 'תוסיף שיעור לקורס', 'תתקן משפט בשיעור'. English: 'build a video course',
  'online course videos', 'animated course lessons'. NOT for one long recorded lesson (lesson-video),
  NOT for a single short reel (dvar-torah-animation), NOT for event footage (event-recap-video).
---

# Course Video Studio - קורס וידאו מונפש מקובץ טקסט

Every lesson is one file, `build/videos/<id>/lesson.py`: `BLOCKS` (what the narrator says) and `CHAPTERS`
(what the screen shows, each scene anchored to words in the narration). Nothing is edited in a video
editor. To change a video you change the file and rebuild.

Talk to the user in Hebrew. Code, commands and file names stay in English.

## 0. Before the first course (once per computer)
Check, and install what is missing yourself:
- Python 3.10+ with `pip install faster-whisper numpy python-docx pillow openpyxl qrcode`
- ffmpeg and ffprobe on PATH
- Node.js 18+ (renders run through `npx hyperframes@0.8.106`, pinned in build_video.py and render_video.py)
- A Gemini API key (`GOOGLE_API_KEY`) in `<course>/.env` or in the environment. Only the user can create it:
  https://aistudio.google.com/apikey
- LibreOffice is optional (PDF of the guide)
- The first narration downloads the Hebrew Whisper model (`ivrit-ai/whisper-large-v3-turbo-ct2`), about 1.6 GB, once.

Costs: narration (Gemini TTS) and illustrations (Gemini flash-lite image) are paid per use. Check the
current prices at https://ai.google.dev/pricing before a large run and tell the user the estimate.
Everything else (Whisper, the render) runs locally for free.

## 1. New course
```
python -X utf8 <skill>/scripts/new_course.py "<course folder>" "<course title>"
```
The folder gets `build/` with the engine, the pipeline and a demo lesson (`demo1`). All commands below run
from inside `build/`. Run `python -X utf8 check_lesson.py demo1` once to confirm the setup.

## 2. Syllabus first, approval before writing
Interview the user briefly: who the learners are, what they should be able to do at the end, how many
levels, and what is out of scope. Then fill `build/course.py`:
- `COURSE` (title, subtitle, brand, instructor), `PARTS` (levels; one is fine), `MODULES` with lessons as
  `(id, title, promise)`, and `FINAL_LESSONS`.
- Ids are short ASCII (`m1l1`, `m2l3`, `bonus1`). The numbering shown on screen is computed from the order.
Show the syllabus as a table and wait for approval. Delete `demo1`/`demo2` from course.py once real lessons exist.

## 3. Facts
Every price, date, name or button label the lessons mention goes into `build/FACTS.md` with its source URL
and the retrieval date. Verify on the web before writing it; mark anything unverified as "לא מאומת" and
keep it out of the narration.

## 4. One lesson, polished, before all the others
Write the first lesson following `references/writing-guide.md`, then:
```
python -X utf8 check_lesson.py m1l1          # static check, no cost. Loop until "ALL LESSONS OK"
python -X utf8 narrate.py m1l1               # TTS per paragraph, Whisper verification, word timing
VID=. python -X utf8 sync_check.py           # reveals out of order inside a beat
VID=. python -X utf8 sync_check2.py          # reveals that fire after their beat ended
python -X utf8 build_video.py m1l1 --lint    # HyperFrames project from the lesson + timing
python -X utf8 render_video.py m1l1 --draft  # fast low-quality preview -> build/qc/draft_m1l1.mp4
```
Show the draft to the user and fix until approved. Only then write the rest of the lessons the same way,
and render them in full:
```
python -X utf8 render_video.py all           # -> <course>/סרטונים/<chapter>/<num> - <title>.mp4 + .jpg
python -X utf8 -u render_queue.py --shard 1/2 > render_queue_1.log 2>&1   # optional: two workers side by side
```
`render_video.py` verifies each delivery (duration matches the audio, 1920x1080, has sound). Skips lessons
already delivered unless `--force`.

## 5. Quality control before handing over
- `python -X utf8 qc_video.py <id>`: a contact sheet, one frame every few seconds. Open it and look.
- `python -X utf8 qc_marks.py <id>`: every screenshot highlight box drawn on its image.
- `python -X utf8 audio_qc.py`: loudness, peaks, silences of the delivered files.
- `python -X utf8 transcribe_check.py <id>`: re-transcribes the delivery and diffs it against the script.
- Generated images: open each one and zoom into small background figures (see the people rules in the guide).

## 6. Documents and preview
Fill `build/doc_content.py` (about, audience, outcomes, FAQ, links), then:
```
python -X utf8 make_docs.py --pdf     # 00 syllabus, 01 upload texts, 02 companion guide (MD + DOCX, guide also PDF)
python -X utf8 make_preview.py        # צפייה בקורס.html - the whole course on one page, plays from disk
python -X utf8 make_review_form.py    # 05 viewing-notes form (Excel) for the user's review pass
```
The guide collects every PROMPT beat and the key points of each lesson automatically.

## Fixing a lesson later
1. Edit `lesson.py`, run `check_lesson.py <id>`.
2. `narrate.py <id>`: only paragraphs whose text changed are re-recorded; the rest come from the cache at no cost.
3. `build_video.py <id>` and `render_video.py <id> --force`.
If only scenes changed, still run narrate (all from cache) so the timing file is newer than the lesson.

## Settings worth knowing
- Voice: `VOICE` and `TTS_MODEL` in narrate.py. Change the voice before the first lesson, not in the middle of a course.
- Pace: about 126 words per minute; `SEC_PER_WORD` in check_lesson.py simulates it before narration.
- Pronunciation: `{display|spoken}` markup in the narration, and `TRANSLIT` in narrate.py for English words.
- Captions hide or fix words through `fixes` and `blocked_names` in the generated video.json (see engine/clean_words.py).
- Look: colours and fonts in `build/clip_template/assets/*.css`; illustration style in `STYLE` of gen_images.py.

## Known traps
- A Hebrew folder path can make headless rendering produce black frames on some machines. If a draft comes
  out black, copy the course to an ASCII path (for example `C:\courses\my-course`) and render there.
- STEPS with 5 cards overflows the screen; use 4 or a list.
- The static checker can pass while a reveal still fires after its beat ended. The two sync checks on the real
  timing catch that; always run them after narration.
- Run Python with `-X utf8` on Windows, or Hebrew output breaks.
