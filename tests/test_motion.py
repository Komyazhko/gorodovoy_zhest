from hand_follower.motion_controller import calculate_command


def test_stops_inside_safe_distance():
    assert calculate_command(1.0, 0)[0:2] == (0.0, 0.0)


def test_caps_linear_speed():
    linear, _ = calculate_command(5.0, 0, max_linear=0.05)
    assert linear <= 0.05
