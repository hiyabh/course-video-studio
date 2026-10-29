# -*- coding: utf-8 -*-
"""Background worker: build + render every narrated lesson that is not delivered yet, in syllabus order.
Keeps polling until all lessons with a lesson.py are delivered (or IDLE_LIMIT passes with nothing to do).

    python -X utf8 -u render_queue.py [--shard K/N] > render_queue.log 2>&1

--shard K/N lets N workers run side by side: worker K takes every N-th lesson in syllabus order.
"""
import sys
import time

import build_video
import render_video
from course import LESSONS, VIDEOS

POLL = 30
IDLE_LIMIT = 3 * 3600


def ready(lid):
    v = VIDEOS / lid
    words, audio = v / "build" / "words.json", v / "clip" / "assets" / "audio" / "lesson.m4a"
    # Narration older than the script means the text changed and is not re-recorded yet.
    return (v / "lesson.py").exists() and words.exists() and audio.exists() and         words.stat().st_mtime >= (v / "lesson.py").stat().st_mtime


def shard():
    if "--shard" not in sys.argv:
        return 0, 1
    k, n = sys.argv[sys.argv.index("--shard") + 1].split("/")
    return int(k), int(n)


def main():
    idle_since, failed = time.time(), set()
    k, n = shard()
    while True:
        todo = [l[0] for i, l in enumerate(LESSONS) if i % n == k and (VIDEOS / l[0] / "lesson.py").exists()]
        pending = [lid for lid in todo if not render_video.out_paths(lid)[0].exists() and lid not in failed]
        if not pending:
            print("QUEUE DONE", "failed:", sorted(failed), flush=True)
            return
        work = [lid for lid in pending if ready(lid)]
        if not work:
            if time.time() - idle_since > IDLE_LIMIT:
                print("QUEUE IDLE TIMEOUT, pending:", pending, flush=True)
                return
            time.sleep(POLL)
            continue
        lid = work[0]
        try:
            if build_video.build(lid, lint=True) and render_video.deliver(lid, force=False):
                print(f"[{lid}] DELIVERED", flush=True)
            else:
                failed.add(lid)
                print(f"[{lid}] FAILED", flush=True)
        except SystemExit as e:
            failed.add(lid)
            print(f"[{lid}] FAILED: {e}", flush=True)
        idle_since = time.time()


if __name__ == "__main__":
    main()
