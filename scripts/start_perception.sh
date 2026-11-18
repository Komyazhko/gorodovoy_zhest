#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
cd "$(dirname "$0")/../ros2_ws"
source install/setup.bash
ros2 run hand_follower perception_node
