from vision.gesture_controller import GestureController

def test_hold_three_seconds():
    g = GestureController(3.0)
    assert not g.update(True, 0.0)
    assert not g.update(True, 2.9)
    assert g.update(True, 3.0)

def test_release_resets_timer():
    g = GestureController(3.0)
    assert not g.update(True, 0.0)
    assert not g.update(False, 2.0)
    assert not g.update(True, 2.1)
