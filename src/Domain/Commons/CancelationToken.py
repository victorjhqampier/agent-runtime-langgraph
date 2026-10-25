import time


class CancelationToken:
    __slots__ = ("deadline",)

    def __init__(self, seconds: float):
        self.deadline = time.monotonic() + seconds

    def remaining(self, floor: float = 0.05) -> float:
        return max(floor, self.deadline - time.monotonic())

    def raise_if_expired(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("SLA_TIMEOUT")
