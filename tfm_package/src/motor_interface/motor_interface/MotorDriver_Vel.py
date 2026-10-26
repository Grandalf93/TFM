#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from dynamixel_sdk import *

from custom_interfaces.msg import WheelSpeed

# Protocol 2.0 control table addresses
OPERATING_MODE_ADDRESS = 11    # 1 Byte (1 = velocity control mode)
TORQUE_ON_ADDRESS = 64         # 1 Byte
GOAL_VELOCITY_ADDRESS = 104    # 4 Bytes

VELOCITY_MODE = 1
MAX_VELOCITY = 1023            # Velocity limit in Dynamixel units


class MotorDriverVel(Node):
    def __init__(self):
        super().__init__('motor_driver_vel')

        # Parameters (use "/dev/ttyUSB0" on Linux or "COM3" on Windows)
        self.declare_parameter('device_name', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 1000000)
        self.declare_parameter('dxl_id_1', 40)
        self.declare_parameter('dxl_id_2', 41)

        device_name = self.get_parameter('device_name').value
        baudrate = self.get_parameter('baudrate').value
        self.dxl_ids = [self.get_parameter('dxl_id_1').value,
                        self.get_parameter('dxl_id_2').value]

        # Initializing Handler objects (one port handles the entire daisy chain)
        self.portHandler = PortHandler(device_name)
        self.packetHandler = PacketHandler(2.0)

        if not self.portHandler.openPort():
            raise RuntimeError(f"Failed to open port {device_name}")
        if not self.portHandler.setBaudRate(baudrate):
            self.portHandler.closePort()
            raise RuntimeError(f"Failed to set baudrate {baudrate}")

        # Disable torque, switch to velocity mode, enable torque
        for dxl_id in self.dxl_ids:
            self.write1(dxl_id, TORQUE_ON_ADDRESS, 0)
            self.write1(dxl_id, OPERATING_MODE_ADDRESS, VELOCITY_MODE)
            self.write1(dxl_id, TORQUE_ON_ADDRESS, 1)

        self.get_logger().info(f"[+] Daisy-chained communication initialized on {device_name}.")
        self.get_logger().info(f"[+] Torque enabled for Motors {self.dxl_ids}.")

        # Subscriber to the wheel speeds published by DiffRobotKinematics
        self.subscription = self.create_subscription(
            WheelSpeed,
            '/wheel_speed_topic',
            self.wheel_speed_callback,
            10
        )

        self.get_logger().info("Listening to /wheel_speed_topic.")

    def check_result(self, dxl_id, dxl_comm_result, dxl_error):
        if dxl_comm_result != COMM_SUCCESS:
            self.get_logger().error(f"Motor {dxl_id} Error: {self.packetHandler.getTxRxResult(dxl_comm_result)}")
            return False
        if dxl_error != 0:
            self.get_logger().error(f"Motor {dxl_id} Status Error: {self.packetHandler.getRxPacketError(dxl_error)}")
            return False
        return True

    def write1(self, dxl_id, address, value):
        result, error = self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, address, value)
        return self.check_result(dxl_id, result, error)

    def wheel_speed_callback(self, msg: WheelSpeed):
        motor_id = msg.id
        if motor_id not in self.dxl_ids:
            self.get_logger().warn(f"Received speed for ID {motor_id}, not one of {self.dxl_ids}")
            return

        # Clamp velocity to the allowed range
        velocity = int(max(-MAX_VELOCITY, min(MAX_VELOCITY, msg.speed_value)))

        self.get_logger().info(f"Motor Velocities {msg.speed_value}")

        result, error = self.packetHandler.write4ByteTxRx(
            self.portHandler, motor_id, GOAL_VELOCITY_ADDRESS, velocity
        )
        if self.check_result(motor_id, result, error):
            self.get_logger().debug(f"Motor {motor_id} velocity set to {velocity}")

    def cleanup(self):
        # Stop motors, disable torque and close the port
        for dxl_id in self.dxl_ids:
            self.packetHandler.write4ByteTxRx(self.portHandler, dxl_id, GOAL_VELOCITY_ADDRESS, 0)
            self.write1(dxl_id, TORQUE_ON_ADDRESS, 0)
        self.portHandler.closePort()
        self.get_logger().info("[+] Torque disabled and port closed.")


def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverVel()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
