#!/usr/bin/env python3

from dynamixel_sdk import *


#Initializing Handler objects
portHandler = PortHandler("COM3")  # your dxl port name
packetHandler = PacketHandler(2.0)  # protocol version

#Opening port
portHandler.openPort()
portHandler.setBaudRate(1000000)

#Enabling torque
dxl_id = 40
torque_on_address = 64
data = 1
packetHandler.write1ByteTxRx(portHandler, dxl_id, torque_on_address, data)

#Get user input
while True:
    try:
        target_position = int(input("Enter target position (0 ~ 4095, -1 to exit): "))
    except ValueError:
        print("Please enter an integer.")
        continue

    if target_position == -1:
        break
    elif target_position < 0 or target_position > 4095:
        print("Position must be between 0 and 4095.")
        continue

    goal_position_address = 116
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, dxl_id, goal_position_address, target_position)
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))