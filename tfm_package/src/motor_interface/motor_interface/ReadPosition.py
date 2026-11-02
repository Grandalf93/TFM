#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import threading


class TwistInput(Node):
    def __init__(self):
        # Create the node with the name 'twist_input'
        super().__init__('twist_input')

        # Create Publisher for /cmd_vel (DiffRobotKinematics subscribes to it)
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info("TwistInput Node has started. Publishing to /cmd_vel.")

        # Start a background thread to handle keyboard input without blocking the ROS 2 executor
        self.input_thread = threading.Thread(target=self.read_keyboard, daemon=True)
        self.input_thread.start()

    def publish_twist(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher_.publish(msg)
        self.get_logger().info(f"Published: linear.x={linear_x:.3f} m/s, angular.z={angular_z:.3f} rad/s")

    def read_keyboard(self):
        print("Enter '<linear_x> <angular_z>' (m/s, rad/s). 's' to stop, 'q' to quit.")
        try:
            while rclpy.ok():
                line = input("> ").strip().lower()
                if line == 'q':
                    # Stop the robot and trigger a clean shutdown of the node
                    self.publish_twist(0.0, 0.0)
                    rclpy.shutdown()
                    break
                if line == 's':
                    self.publish_twist(0.0, 0.0)
                    continue
                try:
                    linear_x, angular_z = (float(v) for v in line.split())
                except ValueError:
                    print("Invalid input. Example: 0.1 0.5")
                    continue
                self.publish_twist(linear_x, angular_z)
        except (KeyboardInterrupt, EOFError):
            self.publish_twist(0.0, 0.0)
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = TwistInput()

    try:
        # rclpy.spin processes your publishes instantly on the main thread
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        # Clean shutdown and stop the robot
        if rclpy.ok():
            node.publish_twist(0.0, 0.0)
            node.destroy_node()
            rclpy.shutdown()
        else:
            try:
                node.destroy_node()
            except Exception:
                pass


if __name__ == '__main__':
    main()
