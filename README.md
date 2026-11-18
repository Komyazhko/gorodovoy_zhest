# Gorodovoy Robot — исправленная интеграционная версия

Платформа: Ubuntu 22.04 / ROS 2 Humble / Python 3.10.

## Важно
Это исправленная программная заготовка с разделёнными ROS-узлами восприятия и управления. Она **не включает движение по умолчанию**:
- RGB и depth должны быть проверены на одной системе координат (aligned depth).
- `depth_scale` необходимо подтвердить для конкретной камеры.
- `/cmd_vel_hand_follower` должен быть добавлен отдельным входом в штатный `twist_mux`.
- Старый `/hand_follower` не удаляется и не останавливается.
- Физический E-STOP обязателен; веб-кнопка не заменяет его.

До завершения этих проверок `depth_aligned` оставляйте `false`, а вход нового контроллера в mux не подключайте.

## Установка на роботе
```bash
sudo apt update
sudo apt install -y ros-humble-cv-bridge ros-humble-sensor-msgs ros-humble-geometry-msgs ros-humble-std-msgs python3-colcon-common-extensions python3-opencv python3-pip
python3 -m pip install -r vision/requirements.txt
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Запуск без движения
Терминал 1:
```bash
source /opt/ros/humble/setup.bash
cd ~/gorodovoy-robot/ros2_ws
source install/setup.bash
ros2 run hand_follower perception_node
```
Терминал 2:
```bash
source /opt/ros/humble/setup.bash
cd ~/gorodovoy-robot/ros2_ws
source install/setup.bash
ros2 run hand_follower follower_node
```
Терминал 3:
```bash
cd ~/gorodovoy-robot
python3 -m vision.app
```
Откройте `http://IP_РОБОТА:5000`.

## ROS-топики
Восприятие публикует:
- `/gorodovoy/target_valid` (`std_msgs/Bool`)
- `/gorodovoy/target_locked` (`std_msgs/Bool`)
- `/gorodovoy/emergency_stop` (`std_msgs/Bool`, true = стоп)
- `/gorodovoy/distance_m` (`std_msgs/Float32`)
- `/gorodovoy/center_error_px` (`std_msgs/Int32`)

Контроллер публикует только `/cmd_vel_hand_follower` (`geometry_msgs/Twist`).
Он не публикует напрямую в `/diff_cont/cmd_vel_unstamped`.

## Переменные среды
Веб-сервер по умолчанию слушает `0.0.0.0:5000`. Для внешней сети используйте только доверенную изолированную сеть робота.
