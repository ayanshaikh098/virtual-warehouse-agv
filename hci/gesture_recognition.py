"""Landmark-based gesture classification and cooldown handling."""
from __future__ import annotations
import time

def classify_landmarks(landmarks) -> str:
    """Classify normalized MediaPipe landmarks as palm, fist, thumbs_up, or two_fingers."""
    # MediaPipe list of 21 landmarks. Fingers extend when tip is farther up (lower y) than PIP.
    if not landmarks or len(landmarks)<21: return "unknown"
    lm=landmarks
    extended=[lm[t].y < lm[p].y-0.035 for t,p in ((8,6),(12,10),(16,14),(20,18))]
    # Distinguish thumbs-up using the thumb's upward axis plus curled fingers.
    thumb_up=lm[4].y < lm[3].y-0.04 and sum(extended)<=1
    if thumb_up: return "thumbs_up"
    count=sum(extended)
    if count>=4: return "open_palm"
    if count==0: return "fist"
    if extended[0] and extended[1] and not any(extended[2:]): return "two_fingers"
    return "unknown"

class GestureDebouncer:
    def __init__(self, cooldown: float=1.0): self.cooldown=cooldown; self.last={}
    def accept(self, gesture: str, now: float|None=None) -> bool:
        if gesture in ("unknown","none"): return False
        now=time.monotonic() if now is None else now
        if now-self.last.get(gesture,-float('inf'))<self.cooldown: return False
        self.last[gesture]=now; return True

GESTURE_ACTIONS={"open_palm":"resume","fist":"pause","thumbs_up":"confirm_destination","two_fingers":"gesture_mode"}
