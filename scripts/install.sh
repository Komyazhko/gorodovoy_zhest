#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions python3-opencv python3-pip
python3 -m pip install -r "$ROOT/vision/requirements.txt"
cd "$ROOT/ros2_ws"
colcon build --symlink-install
echo "Готово. Выполните: source install/setup.bash"
