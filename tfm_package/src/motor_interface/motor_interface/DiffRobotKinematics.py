#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# TODO: Replace 'custom_interfaces' with the name of the package containing your custom message
# and 'WheelSpeed' with the name of your custom message class. Remember custom message contains id (motor)
# and speed_value
from custom_interfaces.msg import WheelSpeed


class DiffRobot(Node):
    def __init__(self):
        # Create the node with the name 'robot'
        super().__init__('kinematics_robot')
        
        # ROS 2 Parameters for easy runtime configuration
        self.declare_parameter('wheel_radius', 0.033)     # meters
        self.declare_parameter('wheelbase', 0.160)        # meters
        self.declare_parameter('rads_to_dxl_unit', 41.7)  # scaling factor
        self.declare_parameter('left_wheel_id', 40)       # ID for left Dynamixel
        self.declare_parameter('right_wheel_id', 41)       # ID for right Dynamixel
        
        # Create Subscriber for /cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Create Publisher for /wheel_speed_topic
        self.publisher_ = self.create_publisher(
            WheelSpeed,
            '/wheel_speed_topic',
            10
        )
        
        self.get_logger().info("DiffRobot Node has started and is listening to /cmd_vel.")

    def cmd_vel_callback(self, msg: Twist):
        # Fetch current parameters
        wheel_radius = self.get_parameter('wheel_radius').value
        wheelbase = self.get_parameter('wheelbase').value
        rads_to_dxl_unit = self.get_parameter('rads_to_dxl_unit').value
        left_id = self.get_parameter('left_wheel_id').value
        right_id = self.get_parameter('right_wheel_id').value
        
        linear_x = msg.linear.x
        angular_z = msg.angular.z

        # 1. Kinematics calculation
        v_left = linear_x - (angular_z * wheelbase / 2.0)
        v_right = linear_x + (angular_z * wheelbase / 2.0)
        
        # 2. Convert to rad/s
        omega_left = v_left / wheel_radius
        omega_right = v_right / wheel_radius
        
        # 3. Convert to raw Dynamixel values (integers)
        dxl_val_left = int(omega_left * rads_to_dxl_unit)
        dxl_val_right = int(omega_right * rads_to_dxl_unit)
        
        # 4. Handle flipped direction of the right motor on the chassis
        dxl_val_right = -dxl_val_right 

        # Create message for Left Motor (ID and Speed)
        left_msg = WheelSpeed()
        left_msg.id = left_id
        left_msg.speed_value = float(dxl_val_left)
        self.publisher_.publish(left_msg)

        # Create message for Right Motor (ID and Speed)
        right_msg = WheelSpeed()
        right_msg.id = right_id
        right_msg.speed_value = float(dxl_val_right)
        self.publisher_.publish(right_msg)
        
        self.get_logger().info(
            f"Published velocities -> Left (ID {left_id}): {dxl_val_left}, Right (ID {right_id}): {dxl_val_right}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = DiffRobot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()