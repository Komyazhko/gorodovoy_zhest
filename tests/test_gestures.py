from vision.gesture_controller import GestureController


def test_locks_after_three_seconds_and_stays_locked():
    controller = GestureController(3.0)
    assert not controller.update(True, now=10.0)
    assert controller.update(True, now=13.1)
    assert controller.update(False, now=14.0)
