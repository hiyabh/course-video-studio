# -*- coding: utf-8 -*-
"""Short constructors for beat specs. Import in build/specs/*.py:  from spec_helpers import *
Every beat after a chapter's first needs `at` = a phrase as transcribed in words.json.
`reveal=[...]` anchors inner elements (items, nodes, chips) to the moment they are said."""

__all__ = ["T", "S", "Q", "SAY", "KW", "KIN", "L", "C", "V", "SRC", "N", "IT", "SPLIT",
           "FLOW", "CYCLE", "TL", "BARS", "SCALE", "VENN", "STACK", "LADDER", "END"]


def _b(t, at, reveal=None, **kw):
    b = {"t": t, **kw}
    if at is not None:
        b["at"] = at
    if reveal:
        b["reveal"] = reveal
    return b


def T(title, eyebrow="", sub=""):
    """Chapter title card (first beat of every chapter): counter + chapter map."""
    return _b("title", None, title=title, eyebrow=eyebrow, sub=sub)


def S(at, img, cap="", sub="", shots=None, **kw):
    """Illustration with Ken Burns, motes and automatic camera moves. shots=[{"at", "focus": [x%, y%], "zoom"}]."""
    return _b("story", at, img=img, cap=cap, sub=sub, **({"shots": shots} if shots is not None else {}), **kw)


def Q(at, text, sub="", reveal=None):
    return _b("question", at, reveal, text=text, sub=sub)


def SAY(at, text, sub="", reveal=None):
    """A spoken line, big. Mark the punch words with *...*."""
    return _b("say", at, reveal, text=text, sub=sub)


def KW(at, big, words, reveal=None, sub=""):
    return _b("keyword", at, reveal, big=big, words=words, sub=sub)


def KIN(at, words, sub="", reveal=None):
    """Kinetic type: each word slams in when spoken (reveal defaults to the words themselves)."""
    return _b("kinetic", at, reveal, words=words, sub=sub)


def L(at, title, items, reveal=None):
    return _b("list", at, reveal, title=title, items=items)


def C(at, rh, rl, lh, ll, mid="מול", reveal=None):
    """Two columns; the right one first, the left one at reveal[0]."""
    return _b("compare", at, reveal, r={"h": rh, "lines": rl}, l={"h": lh, "lines": ll}, mid=mid)


def V(at, q, cite, size=None, reveal=None):
    """A pasuk with niqqud (verify the text before use)."""
    return _b("verse", at, reveal, q=q, cite=cite, **({"size": size} if size else {}))


def SRC(at, q, cite, size=None, reveal=None):
    return _b("source", at, reveal, q=q, cite=cite, **({"size": size} if size else {}))


def N(at, n, label, sub="", suffix="", reveal=None):
    return _b("number", at, reveal, n=n, label=label, sub=sub, suffix=suffix)


def IT(at, img, title, lines, reveal=None):
    return _b("imgtext", at, reveal, img=img, title=title, lines=lines)


def SPLIT(at, img, q, cite="", reveal=None):
    return _b("split", at, reveal, img=img, q=q, cite=cite)


def FLOW(at, nodes, title="", reveal=None):
    """Arrows between 2-5 nodes, right to left, each node at its reveal."""
    return _b("flow", at, reveal, nodes=nodes, title=title)


def CYCLE(at, nodes, title="", center="", reveal=None):
    """3-6 nodes on a circle with arcs; the closing arc and the centre label come last."""
    return _b("cycle", at, reveal, nodes=nodes, title=title, center=center)


def TL(at, items, dates=None, title="", reveal=None):
    """Timeline right to left; dates (optional) print above/below each point."""
    return _b("timeline", at, reveal, items=items, title=title, **({"dates": dates} if dates else {}))


def BARS(at, bars, title="", reveal=None):
    """bars=[{"label", "value", "suffix"}]; bars grow and count up."""
    return _b("bars", at, reveal, bars=bars, title=title)


def SCALE(at, r, l, tilt="0", title="", reveal=None):
    """Balance: right pan, left pan, then tilt 'r'/'l'/'0' (reveal = [right, left, tilt])."""
    return _b("scale", at, reveal, r=r, l=l, tilt=tilt, title=title)


def VENN(at, r, l, mid, title="", reveal=None):
    return _b("venn", at, reveal, r=r, l=l, mid=mid, title=title)


def STACK(at, items, title="", reveal=None):
    """Blocks drop and stack bottom-up (first item = base)."""
    return _b("stack", at, reveal, items=items, title=title)


def LADDER(at, steps, title="", reveal=None):
    """Rising steps right to left, a marker climbs to each."""
    return _b("ladder", at, reveal, steps=steps, title=title)


def END(at, title, eyebrow="", sub=""):
    return _b("closing", at, title=title, eyebrow=eyebrow, sub=sub)


# ---- course beats ----
__all__ += ["LINK", "PHONE"]


def PHONE(at, steps, title="השיחה במחשב", sub="", reveal=None):
    """Phone mockup of the Claude app (Code tab) showing a conversation that runs on the computer.
    steps = [you(..), say(..), done(..), ask(..)]; reveal = one phrase per step."""
    return _b("phone", at, reveal, steps=steps, title=title, sub=sub)


def LINK(at, title, url, sub="", icon="🔗", reveal=None):
    """A link card with a scannable QR code. Say the place, never read the address: 'הקישור מופיע מתחת לסרטון'."""
    return _b("link", at, reveal, title=title, url=url, sub=sub, icon=icon)


__all__ += ["APP", "SHOT", "FILES", "PROMPT", "STEPS", "LT", "you", "say", "tool", "done", "file", "ask"]


def LT(badge, title, sub="", eyebrow=""):
    """Lesson title card (first beat of a lesson): badge like 'שיעור 2.3'."""
    return _b("title", None, title=title, eyebrow=eyebrow, sub=sub, badge=badge)


def APP(at, steps, folder="My folder", mode="Manual", model="Opus 5.5", hi=None, reveal=None, **kw):
    """Animated Claude Code desktop window. steps = [you(..), tool(..), ask(..), say(..), done(..), file(..)].
    reveal = one phrase per step, then one per highlight. hi = [{"el": "folder|mode|model|input|plus|env|code|scheduled|customize"}]."""
    return _b("app", at, reveal, steps=steps, folder=folder, mode=mode, model=model, hi=hi or [], **kw)


def you(text):
    return {"k": "you", "text": text}


def say(text):
    return {"k": "say", "text": text}


def tool(name, text):
    return {"k": "tool", "tool": name, "text": text}


def done(text):
    return {"k": "done", "text": text}


def file(name, sub="", icon="📄"):
    return {"k": "file", "text": name, "sub": sub, "icon": icon}


def ask(text, detail="", think=1.6, click="yes"):
    """Permission card. click="no" animates a click on the Deny button instead of Allow."""
    return {"k": "ask", "text": text, "detail": detail, "think": think, "click": click}


def SHOT(at, img, url="", marks=None, reveal=None, title=""):
    """Real screenshot (common/shots/<img>) in a window; marks=[{"box": [x%, y%, w%, h%], "label", "zoom"}]."""
    return _b("shot", at, reveal, img=img, url=url, marks=marks or [], title=title)


def FILES(at, files, folders, title="", reveal=None, icon="📄"):
    """Messy files fly into folders at reveal[0]. folders=[{"name", "items": [file indices]}]."""
    return _b("files", at, reveal, files=files, folders=folders, title=title, icon=icon)


def PROMPT(at, text, title="נסו בעצמכם", note="", reveal=None):
    return _b("prompt", at, reveal, text=text, title=title, note=note)


def STEPS(at, steps, title="", reveal=None):
    """steps=[{"h", "d", "icon"}] as numbered cards, right to left."""
    return _b("steps", at, reveal, steps=steps, title=title)
