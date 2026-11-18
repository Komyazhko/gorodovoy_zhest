# Gorodovoy Robot

Базовый проект управления мобильным роботом по жесту поднятой руки. Целевая платформа: Ubuntu 22.04, ROS 2 Humble, Python 3.10.

## Важно перед запуском на роботе

Это интеграционная заготовка, а не подтверждённая аппаратная сборка. До движения необходимо проверить реальные RGB/depth topics, совмещение изображений, единицы глубины, frame_id, знак угловой скорости и вход `twist_mux`. Первый тест проводите на минимальной скорости в безопасной зоне с готовой физической аварийной остановкой.

## Установка

```bash
sudo apt update
sudo apt install -y ros-humble-ros-base python3-colcon-common-extensions python3-opencv python3-pip
cd ~/gorodovoy-robot
python3 -m pip install -r vision/requirements.txt
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Проверка ROS

```bash
source /opt/ros/humble/setup.bash
ros2 topic list
ros2 topic info /camera_depth/image_raw
ros2 topic info /camera_depth/depth/image_raw
ros2 topic info /diff_cont/cmd_vel_unstamped
```

## Запуск

ROS-узел в отдельном терминале:

```bash
source /opt/ros/humble/setup.bash
cd ~/gorodovoy-robot/ros2_ws
source install/setup.bash
ros2 run hand_follower follower_node
```

Веб-сервер в другом терминале:

```bash
cd ~/gorodovoy-robot
python3 -m vision.app
```

Откройте `http://IP_РОБОТА:5000`.

## Архитектура движения

Узел публикует только в `/cmd_vel_hand_follower`. Этот topic требуется отдельно добавить во входы штатного `twist_mux` с подходящим приоритетом. Не публикуйте напрямую в `/diff_cont/cmd_vel_unstamped` и не заменяйте штатный драйвер.

Для реального следования ещё требуется подключить распознавание человека/руки и ROS-публикацию входных данных:
- `/hand_follower/target_valid` (`std_msgs/Bool`)
- `/hand_follower/target_locked` (`std_msgs/Bool`)
- `/hand_follower/emergency_stop` (`std_msgs/Bool`)
- `/hand_follower/distance_m` (`std_msgs/Float32`)
- `/hand_follower/center_error_px` (`std_msgs/Int32`)

Поднятая рука должна удерживаться 3 секунды; после фиксации цели опускание руки не отменяет текущую команду. Потеря цели или устаревшая глубина приводит к нулевой скорости.

## Безопасность

`safe_stop_distance_m` по умолчанию 1.2 м. В `config/robot.yaml` указан `depth_scale: 0.001` как распространённый вариант для 16UC1, но его обязательно подтвердить измерением на конкретной камере. Веб-кнопка STOP не заменяет физический E-STOP.
