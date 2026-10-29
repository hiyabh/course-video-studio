#!/usr/bin/env bash
# Full pipeline for every lesson that has a lesson.py: check -> narrate -> build -> render -> docs.
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8
python -X utf8 check_lesson.py "$@"
python -X utf8 -u narrate.py "$@"
python -X utf8 build_video.py "$@" --lint
python -X utf8 -u render_video.py "$@"
python -X utf8 make_docs.py --pdf
