import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, Float32, Int32

class HandFollowerNode(Node):
    def __init__(self):
        super().__init__('hand_follower')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_hand_follower')
        self.declare_parameter('safe_stop_distance_m', 1.2)
        self.declare_parameter('max_linear_speed_mps', 0.12)
        self.declare_parameter('max_angular_speed_rps', 0.35)
        self.declare_parameter('linear_gain', 0.35)
        self.declare_parameter('angular_gain', 0.8)
        self.declare_parameter('target_timeout_sec', 0.8)
        self.declare_parameter('center_deadband_px', 35)
        gp = lambda n: self.get_parameter(n).value
        self.safe_distance = float(gp('safe_stop_distance_m'))
        self.max_linear = float(gp('max_linear_speed_mps'))
        self.max_angular = float(gp('max_angular_speed_rps'))
        self.linear_gain = float(gp('linear_gain'))
        self.angular_gain = float(gp('angular_gain'))
        self.timeout = float(gp('target_timeout_sec'))
        self.deadband = int(gp('center_deadband_px'))
        self.target_valid = False
        self.target_locked = False
        self.emergency_stop = True
        self.distance_m = None
        self.center_error_px = 0
        self.target_stamp = 0.0
        self.depth_stamp = 0.0
        self.create_subscription(Bool, '/hand_follower/target_valid', self.on_target, 10)
        self.create_subscription(Bool, '/hand_follower/target_locked', self.on_locked, 10)
        self.create_subscription(Bool, '/hand_follower/emergency_stop', self.on_estop, 10)
        self.create_subscription(Float32, '/hand_follower/distance_m', self.on_depth, 10)
        self.create_subscription(Int32, '/hand_follower/center_error_px', self.on_error, 10)
        self.pub = self.create_publisher(Twist, gp('cmd_vel_topic'), 10)
        self.create_timer(0.05, self.control)
        self.get_logger().info('Hand follower publishes to dedicated twist_mux input')

    def on_target(self, msg):
        self.target_valid = bool(msg.data)
        if self.target_valid:
            self.target_stamp = time.monotonic()

    def on_locked(self, msg):
        self.target_locked = bool(msg.data)

    def on_estop(self, msg):
        self.emergency_stop = bool(msg.data)

    def on_depth(self, msg):
        if float(msg.data) > 0:
            self.distance_m = float(msg.data)
            self.depth_stamp = time.monotonic()

    def on_error(self, msg):
        self.center_error_px = int(msg.data)

    def stop(self):
        self.pub.publish(Twist())

    def control(self):
        now = time.monotonic()
        fresh_target = self.target_valid and now-self.target_stamp <= self.timeout
        fresh_depth = self.distance_m is not None and now-self.depth_stamp <= self.timeout
        if self.emergency_stop or not self.target_locked or not fresh_target or not fresh_depth:
            self.stop()
            return
        cmd = Twist()
        if abs(self.center_error_px) > self.deadband:
            cmd.angular.z = max(-self.max_angular, min(
                self.max_angular, -self.angular_gain*self.center_error_px/320.0))
        if self.distance_m > self.safe_distance:
            cmd.linear.x = max(0.0, min(
                self.max_linear, self.linear_gain*(self.distance_m-self.safe_distance)))
        else:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
        self.pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = HandFollowerNode()
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
