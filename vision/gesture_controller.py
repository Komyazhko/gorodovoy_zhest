import time


class GestureController:
    def __init__(self, hold_seconds=3.0):
        self.hold_seconds = float(hold_seconds)
        self.raised_since = None
        self.locked = False

    def update(self, hand_raised, now=None):
        now = time.monotonic() if now is None else now
        if self.locked:
            return True
        if hand_raised:
            if self.raised_since is None:
                self.raised_since = now
            if now - self.raised_since >= self.hold_seconds:
                self.locked = True
        else:
            self.raised_since = None
        return self.locked

    def reset(self):
        self.raised_since = None
        self.locked = False
