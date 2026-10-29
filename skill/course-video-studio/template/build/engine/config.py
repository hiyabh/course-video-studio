# -*- coding: utf-8 -*-
"""Per-video settings. Every engine script runs with VID=<videos/<id>> in the environment."""
import json
import os
from pathlib import Path

VID = Path(os.environ["VID"]).resolve()
BUILD = VID / "build"
CLIP = VID / "clip"
CFG = json.loads((BUILD / "video.json").read_text(encoding="utf-8"))

TITLE = CFG["title"]
SUBTITLE = CFG.get("subtitle", "")
AUDIO = CLIP / "assets" / "audio" / "lesson.m4a"
MAX_GAP = CFG.get("density_max_gap", 12)
