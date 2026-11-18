#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/humble/setup.bash
cd "$ROOT/ros2_ws"
source install/setup.bash
ros2 run hand_follower follower_node
