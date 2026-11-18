from hand_follower.motion_controller import calculate_command

def test_stop_inside_safe_distance():
    assert calculate_command(1.0, 0) == (0.0, 0.0)

def test_move_when_far():
    linear, angular = calculate_command(2.0, 0)
    assert linear > 0 and angular == 0
