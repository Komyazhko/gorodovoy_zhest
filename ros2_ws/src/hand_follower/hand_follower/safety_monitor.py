import time

class FreshnessMonitor:
    def __init__(self, timeout_sec=0.8):
        self.timeout_sec = timeout_sec
        self.target_stamp = None
        self.depth_stamp = None

    def target_updated(self):
        self.target_stamp = time.monotonic()

    def depth_updated(self):
        self.depth_stamp = time.monotonic()

    def safe(self, now=None):
        now = time.monotonic() if now is None else now
        return (self.target_stamp is not None and self.depth_stamp is not None
                and now-self.target_stamp <= self.timeout_sec
                and now-self.depth_stamp <= self.timeout_sec)
