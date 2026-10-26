#!/usr/bin/env python3

from dynamixel_sdk import *



'''
NOTE: It must include a /wheel_speeds subscriber in order to receive the velocity to be commanded
'''

# === CONFIGURATION ===
# 1. Double check which COM port your U2D2 or USB adapter is on using Device Manager!
DEVICE_NAME = "/dev/ttyUSB0"          # Change to "COM4" or whichever port your device uses
BAUDRATE = 1000000            # Ensure this matches your Dynamixel's configured baud rate
PROTOCOL_VERSION = 2.0        # 2.0 for X-Series (XM, XL, XC, etc.) or MX with 2.0 firmware

# Motor IDs on the daisy chain
dxl_id_1 = 40
dxl_id_2 = 41

# Protocol 2.0 control table addresses
torque_on_address = 64        # 1 Byte
goal_position_address = 116   # 4 Bytes

# Initialize PortHandler & PacketHandler
portHandler = PortHandler(DEVICE_NAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open Port
if portHandler.openPort():
    print(f"[+] Succeeded to open port: {DEVICE_NAME}")
else:
    print(f"[-] Failed to open port: {DEVICE_NAME}")
    print("[*] Troubleshooting Tip: Make sure Dynamixel Wizard or other scripts are CLOSED.")
    quit()

# Set Baudrate
if portHandler.setBaudRate(BAUDRATE):
    print(f"[+] Succeeded to set the baudrate to: {BAUDRATE} bps")
else:
    print("[-] Failed to set the baudrate!")
    portHandler.closePort()
    quit()

# === TORQUE ENABLING ===
# Enable Torque for Motor 1
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, dxl_id_1, torque_on_address, 1)
if dxl_comm_result != COMM_SUCCESS:
    print(f"[-] Motor {dxl_id_1} Torque Enable Comm Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
elif dxl_error != 0:
    print(f"[-] Motor {dxl_id_1} Torque Enable Status Error: {packetHandler.getRxPacketError(dxl_error)}")
else:
    print(f"[+] Torque successfully enabled for Motor {dxl_id_1}")

# Enable Torque for Motor 2
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, dxl_id_2, torque_on_address, 1)
if dxl_comm_result != COMM_SUCCESS:
    print(f"[-] Motor {dxl_id_2} Torque Enable Comm Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
elif dxl_error != 0:
    print(f"[-] Motor {dxl_id_2} Torque Enable Status Error: {packetHandler.getRxPacketError(dxl_error)}")
else:
    print(f"[+] Torque successfully enabled for Motor {dxl_id_2}")


# === MAIN CONTROL LOOP ===
try:
    while True:
        try:
            user_input = input(f"Enter target positions (e.g., '0 4095' or -1 to exit): ").strip()
            
            # Check if user wants to exit
            if user_input == "-1":
                break
            
            parts = user_input.split()
            if len(parts) != 2:
                print("Please enter exactly TWO integers separated by a space (or -1 to exit).")
                continue
                
            target_pos_1 = int(parts[0])
            target_pos_2 = int(parts[1])
            
        except ValueError:
            print("Please enter integers only.")
            continue

        # Range check for inputs
        if (target_pos_1 < 0 or target_pos_1 > 4095) or (target_pos_2 < 0 or target_pos_2 > 4095):
            print("Positions must be between 0 and 4095.")
            continue

        # Write to Motor 1
        dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, dxl_id_1, goal_position_address, target_pos_1)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"[-] Motor {dxl_id_1} Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
        elif dxl_error != 0:
            print(f"[-] Motor {dxl_id_1} Status Error: {packetHandler.getRxPacketError(dxl_error)}")
        else:
            print(f"[+] Motor {dxl_id_1} moved to {target_pos_1}")

        # Write to Motor 2
        dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, dxl_id_2, goal_position_address, target_pos_2)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"[-] Motor {dxl_id_2} Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
        elif dxl_error != 0:
            print(f"[-] Motor {dxl_id_2} Status Error: {packetHandler.getRxPacketError(dxl_error)}")
        else:
            print(f"[+] Motor {dxl_id_2} moved to {target_pos_2}")

finally:
    # Graceful shutdown: Always free resources and torque when script ends
    print("\n[*] Disabling torque and closing serial port...")
    packetHandler.write1ByteTxRx(portHandler, dxl_id_1, torque_on_address, 0)
    packetHandler.write1ByteTxRx(portHandler, dxl_id_2, torque_on_address, 0)
    portHandler.closePort()
    print("[+] Cleanup complete. Port closed.")