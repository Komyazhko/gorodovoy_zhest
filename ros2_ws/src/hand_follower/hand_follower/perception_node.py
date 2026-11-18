import json
import os
import tempfile
import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, Float32, Int32

try:
    import mediapipe as mp
except ImportError:
    mp = None


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('gorodovoy_perception')

        self.declare_parameter('rgb_topic', '/camera_depth/image_raw')
        self.declare_parameter('depth_topic', '/camera_depth/depth/image_raw')
        self.declare_parameter('depth_scale', 0.001)
        self.declare_parameter('depth_aligned', False)
        self.declare_parameter('min_valid_depth_m', 0.25)
        self.declare_parameter('max_valid_depth_m', 5.0)
        self.declare_parameter('target_lock_seconds', 3.0)
        self.declare_parameter('state_file', '/tmp/gorodovoy_state.json')
        self.declare_parameter('estop_file', '/tmp/gorodovoy_estop')

        get = lambda n: self.get_parameter(n).value
        self.depth_scale = float(get('depth_scale'))
        self.depth_aligned = bool(get('depth_aligned'))
        self.min_depth = float(get('min_valid_depth_m'))
        self.max_depth = float(get('max_valid_depth_m'))
        self.lock_seconds = float(get('target_lock_seconds'))
        self.state_file = str(get('state_file'))
        self.estop_file = str(get('estop_file'))

        self.bridge = CvBridge()
        self.rgb = None
        self.depth = None
        self.depth_encoding = None
        self.raised_since = None
        self.locked = False
        self.last_person_stamp = 0.0
        self.last_depth_stamp = 0.0
        self.distance_m = None
        self.center_error = 0
        self.target_valid = False

        self.pub_valid = self.create_publisher(Bool, '/gorodovoy/target_valid', 10)
        self.pub_locked = self.create_publisher(Bool, '/gorodovoy/target_locked', 10)
        self.pub_estop = self.create_publisher(Bool, '/gorodovoy/emergency_stop', 10)
        self.pub_distance = self.create_publisher(Float32, '/gorodovoy/distance_m', 10)
        self.pub_error = self.create_publisher(Int32, '/gorodovoy/center_error_px', 10)

        self.create_subscription(Image, get('rgb_topic'), self.on_rgb, 10)
        self.create_subscription(Image, get('depth_topic'), self.on_depth, 10)
        self.create_timer(0.1, self.process)

        self.pose = None
        if mp is not None:
            self.pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=0,
                enable_segmentation=False,
                min_detection_confidence=0.55,
                min_tracking_confidence=0.55,
            )
        else:
            self.get_logger().error('MediaPipe is not installed; person/pose detection is disabled.')

        self.get_logger().warning(
            'Perception started. depth_aligned=%s. Motion must remain disabled '
            'until RGB/depth alignment and depth units are verified.' % self.depth_aligned
        )

    def on_rgb(self, msg):
        try:
            self.rgb = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().error('RGB conversion failed: %s' % exc)

    def on_depth(self, msg):
        try:
            self.depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            self.depth_encoding = msg.encoding
            self.last_depth_stamp = time.monotonic()
        except Exception as exc:
            self.get_logger().error('Depth conversion failed: %s' % exc)

    def estimate_distance(self, landmarks, width, height):
        if not self.depth_aligned or self.depth is None:
            return None
        if self.depth.shape[:2] != (height, width):
            return None

        # Sample a central torso region; use median to reject isolated invalid pixels.
        xs = [landmarks[i].x for i in (11, 12, 23, 24)]
        ys = [landmarks[i].y for i in (11, 12, 23, 24)]
        cx = int(np.mean(xs) * width)
        cy = int(np.mean(ys) * height)
        x1, x2 = max(0, cx - 12), min(width, cx + 13)
        y1, y2 = max(0, cy - 18), min(height, cy + 19)
        roi = self.depth[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        values = roi.astype(np.float32)
        if self.depth_encoding in ('16UC1', 'mono16'):
            values *= self.depth_scale
        elif self.depth_encoding == '32FC1':
            pass
        else:
            return None

        valid = values[np.isfinite(values) & (values >= self.min_depth) & (values <= self.max_depth)]
        if valid.size < 8:
            return None
        return float(np.median(valid))

    def write_state(self, state):
        directory = os.path.dirname(self.state_file) or '/tmp'
        os.makedirs(directory, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix='gorodovoy_', dir=directory)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(state, stream)
            os.replace(temp_path, self.state_file)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def process(self):
        now = time.monotonic()
        frame = self.rgb
        person_found = False
        distance = None

        if frame is not None and self.pose is not None:
            height, width = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.pose.process(rgb)
            if result.pose_landmarks:
                lm = result.pose_landmarks.landmark
                # COCO/MediaPipe Pose indices: shoulders 11/12, wrists 15/16.
                left_raised = lm[15].visibility > 0.55 and lm[15].y < lm[11].y
                right_raised = lm[16].visibility > 0.55 and lm[16].y < lm[12].y
                person_found = (
                    lm[11].visibility > 0.55 and lm[12].visibility > 0.55
                    and lm[23].visibility > 0.45 and lm[24].visibility > 0.45
                )
                if person_found:
                    self.last_person_stamp = now
                    self.target_valid = True
                    center_x = (lm[23].x + lm[24].x) * 0.5 * width
                    self.center_error = int(center_x - width * 0.5)
                    distance = self.estimate_distance(lm, width, height)
                    if left_raised or right_raised:
                        if self.raised_since is None:
                            self.raised_since = now
                        if now - self.raised_since >= self.lock_seconds:
                            self.locked = True
                    elif not self.locked:
                        self.raised_since = None
                else:
                    self.target_valid = False
            else:
                self.target_valid = False
        else:
            self.target_valid = False

        target_fresh = self.target_valid and now - self.last_person_stamp <= 0.8
        depth_fresh = self.last_depth_stamp > 0 and now - self.last_depth_stamp <= 0.8
        if distance is not None:
            self.distance_m = distance

        # Fail closed: missing pose, depth, unverified alignment, or missing operator enable => stop.
        operator_enabled = os.path.exists(self.estop_file)
        emergency = not (
            operator_enabled and self.depth_aligned and target_fresh
            and depth_fresh and self.distance_m is not None
        )

        self.pub_valid.publish(Bool(data=bool(target_fresh)))
        self.pub_locked.publish(Bool(data=bool(self.locked)))
        self.pub_estop.publish(Bool(data=bool(emergency)))
        if self.distance_m is not None and depth_fresh and self.depth_aligned:
            self.pub_distance.publish(Float32(data=float(self.distance_m)))
        else:
            self.distance_m = None
        self.pub_error.publish(Int32(data=int(self.center_error)))

        annotated = frame.copy() if frame is not None else None
        if annotated is not None:
            cv2.putText(
                annotated,
                'LOCKED' if self.locked else ('TARGET' if target_fresh else 'NO TARGET'),
                (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 0) if target_fresh else (0, 0, 255), 2
            )
            if self.distance_m is not None:
                cv2.putText(annotated, 'Depth: %.2f m' % self.distance_m, (12, 56),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            ok, encoded = cv2.imencode('.jpg', annotated)
            if ok:
                # Store JPEG alongside state for the Flask dashboard.
                image_path = self.state_file.rsplit('.', 1)[0] + '.jpg'
                temp = image_path + '.tmp'
                encoded.tofile(temp)
                os.replace(temp, image_path)

        self.write_state({
            'target_valid': bool(target_fresh),
            'target_locked': bool(self.locked),
            'emergency_stop': bool(emergency),
            'distance_m': self.distance_m,
            'center_error_px': int(self.center_error),
            'depth_aligned': self.depth_aligned,
            'operator_enabled': operator_enabled,
            'status': 'STOP' if emergency else 'READY',
        })

    def destroy_node(self):
        if self.pose is not None:
            self.pose.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
