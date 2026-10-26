#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TwistInput(Node):
    def __init__(self):
        # Create the node with the name 'twist_input'
        super().__init__('twist_input')

        # Create Publisher for /cmd_vel (DiffRobotKinematics subscribes to it)
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info("TwistInput Node has started. Publishing to /cmd_vel.")

    def publish_twist(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher_.publish(msg)
        self.get_logger().info(f"Published: linear.x={linear_x:.3f} m/s, angular.z={angular_z:.3f} rad/s")


def main(args=None):
    rclpy.init(args=args)
    node = TwistInput()

    print("Enter '<linear_x> <angular_z>' (m/s, rad/s). 's' to stop, 'q' to quit.")
    try:
        while rclpy.ok():
            line = input("> ").strip().lower()
            if line == 'q':
                break
            if line == 's':
                node.publish_twist(0.0, 0.0)
                continue
            try:
                linear_x, angular_z = (float(v) for v in line.split())
            except ValueError:
                print("Invalid input. Example: 0.1 0.5")
                continue
            node.publish_twist(linear_x, angular_z)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        # Stop the robot before exiting
        node.publish_twist(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
