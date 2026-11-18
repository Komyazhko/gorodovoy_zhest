#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 topic list
ros2 topic info /cmd_vel_hand_follower || true
ros2 topic info /diff_cont/cmd_vel_unstamped || true
