#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
cd "$(dirname "$0")/../ros2_ws"
colcon build --symlink-install
