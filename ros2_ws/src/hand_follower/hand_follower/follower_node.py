import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, Float32, Int32

from .motion_controller import calculate_command


class GorodovoyFollowerNode(Node):
    def __init__(self):
        super().__init__('gorodovoy_hand_follower')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel_hand_follower')
        self.declare_parameter('safe_stop_distance_m', 1.2)
        self.declare_parameter('max_linear_speed_mps', 0.05)
        self.declare_parameter('max_angular_speed_rps', 0.15)
        self.declare_parameter('linear_gain', 0.20)
        self.declare_parameter('angular_gain', 0.50)
        self.declare_parameter('target_timeout_sec', 0.8)
        self.declare_parameter('depth_timeout_sec', 0.8)
        self.declare_parameter('center_deadband_px', 35)

        p = lambda name: self.get_parameter(name).value
        self.safe_distance = float(p('safe_stop_distance_m'))
        self.max_linear = float(p('max_linear_speed_mps'))
        self.max_angular = float(p('max_angular_speed_rps'))
        self.linear_gain = float(p('linear_gain'))
        self.angular_gain = float(p('angular_gain'))
        self.target_timeout = float(p('target_timeout_sec'))
        self.depth_timeout = float(p('depth_timeout_sec'))
        self.deadband = int(p('center_deadband_px'))

        self.target_valid = False
        self.target_locked = False
        self.emergency_stop = True
        self.distance_m = None
        self.center_error_px = 0
        self.target_stamp = 0.0
        self.depth_stamp = 0.0

        self.create_subscription(Bool, '/gorodovoy/target_valid', self.on_target, 10)
        self.create_subscription(Bool, '/gorodovoy/target_locked', self.on_locked, 10)
        self.create_subscription(Bool, '/gorodovoy/emergency_stop', self.on_estop, 10)
        self.create_subscription(Float32, '/gorodovoy/distance_m', self.on_depth, 10)
        self.create_subscription(Int32, '/gorodovoy/center_error_px', self.on_error, 10)

        self.pub = self.create_publisher(Twist, p('cmd_vel_topic'), 10)
        self.create_timer(0.05, self.control)
        self.get_logger().warning(
            'Safe-start enabled: motion is inhibited until perception, depth, '
            'and E-stop state are valid. Output: %s' % p('cmd_vel_topic')
        )

    def on_target(self, msg):
        self.target_valid = bool(msg.data)
        if self.target_valid:
            self.target_stamp = time.monotonic()

    def on_locked(self, msg):
        self.target_locked = bool(msg.data)

    def on_estop(self, msg):
        self.emergency_stop = bool(msg.data)

    def on_depth(self, msg):
        value = float(msg.data)
        if value > 0.0:
            self.distance_m = value
            self.depth_stamp = time.monotonic()

    def on_error(self, msg):
        self.center_error_px = int(msg.data)

    def stop(self):
        self.pub.publish(Twist())

    def control(self):
        now = time.monotonic()
        target_fresh = self.target_valid and now - self.target_stamp <= self.target_timeout
        depth_fresh = self.distance_m is not None and now - self.depth_stamp <= self.depth_timeout

        if self.emergency_stop or not self.target_locked or not target_fresh or not depth_fresh:
            self.stop()
            return

        linear, angular = calculate_command(
            self.distance_m,
            self.center_error_px,
            self.safe_distance,
            self.max_linear,
            self.max_angular,
            self.linear_gain,
            self.angular_gain,
            self.deadband,
        )
        cmd = Twist()
        cmd.linear.x = linear
        cmd.angular.z = angular
        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = GorodovoyFollowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
