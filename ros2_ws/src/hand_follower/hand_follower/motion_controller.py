def calculate_command(distance_m, center_error_px, safe_distance_m=1.2,
                      max_linear=0.12, max_angular=0.35,
                      linear_gain=0.35, angular_gain=0.8, deadband_px=35):
    if distance_m is None or distance_m <= 0:
        return 0.0, 0.0
    angular = 0.0
    if abs(center_error_px) > deadband_px:
        angular = max(-max_angular, min(
            max_angular, -angular_gain*center_error_px/320.0))
    linear = 0.0
    if distance_m > safe_distance_m:
        linear = max(0.0, min(max_linear, linear_gain*(distance_m-safe_distance_m)))
    else:
        angular = 0.0
    return linear, angular
