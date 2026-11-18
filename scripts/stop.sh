#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 topic pub --once /cmd_vel_hand_follower geometry_msgs/msg/Twist '{}'
