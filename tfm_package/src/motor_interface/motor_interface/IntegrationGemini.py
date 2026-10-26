# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "dynamixel-sdk>=4.1.0",
#     "google-genai>=2.29.0",
#     "pillow>=12.3.0",
# ]
# ///
import os
import time
from PIL import Image
from google import genai
from google.genai import types
from dynamixel_sdk import *

# --- DYNAMIXEL CONFIGURATION (XM Series, Protocol 2.0) ---
ADDR_TORQUE_ENABLE    = 64
ADDR_GOAL_POSITION    = 116
ADDR_PRESENT_POSITION = 132
PROTOCOL_VERSION      = 2.0

DXL1_ID               = 40               # Motor 1 (Pan/Base Joint)
DXL2_ID               = 41               # Motor 2 (Tilt/Shoulder Joint)
BAUDRATE              = 1000000
DEVICENAME            = 'COM4'  # Use 'COM3' on Windows

TORQUE_ENABLE         = 1
TORQUE_DISABLE        = 0

# --- GEMINI CLIENT SETUP ---
# Make sure GEMINI_API_KEY environment variable is set
client = genai.Client()

# --- INITIALIZE DYNAMIXEL HARDWARE ---
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort() or not portHandler.setBaudRate(BAUDRATE):
    print("Failed to initialize Dynamixel hardware. Check connection/port.")
    quit()

# Enable Torque for both motors
packetHandler.write1ByteTxRx(portHandler, DXL1_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
packetHandler.write1ByteTxRx(portHandler, DXL2_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
print("Dynamixel Hardware initialized and Torque Enabled.")


# --- DEFINE HARDWARE TOOL FOR GEMINI ---
# Describe the physical action Gemini is allowed to perform
move_motor_tool = types.FunctionDeclaration(
    name="move_motor",
    description="Moves a Dynamixel motor to a goal position.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "motor_id": {
                "type": "INTEGER", 
                "description": "The ID of the motor to move. ID 40 represents Pan (horizontal axis), ID 41 represents Tilt (vertical axis)."
            },
            "position": {
                "type": "INTEGER", 
                "description": "Target encoder position. Must be within the safe range of 1024 (left/down) to 3072 (right/up). 2048 is centered."
            }
        },
        "required": ["motor_id", "position"]
    }
)

tools_list = types.Tool(function_declarations=[move_motor_tool])


# --- CORE INTEGRATION LOOP ---
def execute_motor_movement(motor_id: int, position: int):
    """Saves safety limits and executes the API command directly on the Dynamixel motors."""
    # Local safety guard: keep motor bounds strictly within 1024 - 3072
    safe_position = max(1024, min(3072, position))
    
    print(f"[ACTION] Writing safe position {safe_position} to Motor ID {motor_id}...")
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(
        portHandler, motor_id, ADDR_GOAL_POSITION, safe_position
    )
    
    if dxl_comm_result != COMM_SUCCESS:
        return f"Error communicating: {packetHandler.getTxRxResult(dxl_comm_result)}"
    elif dxl_error != 0:
        return f"Hardware error: {packetHandler.getRxPacketError(dxl_error)}"
    return f"Success: Motor {motor_id} moved to position {safe_position}"


try:
    print("\nQuerying Gemini Robotics ER for task planning...")
    
    # Send a mock spatial prompt (Or use a camera image captured live from your robot)
    # response = client.models.generate_content( ... , contents=[ "image.jpg", "Point the camera..." ] )
    
    response = client.models.generate_content(
        model="gemini-robotics-er-2-preview",
        contents=[
            "Set Motor 40 (Pan) halfway to the right (position 2560) and center Motor 41 (Tilt) to position 2048."
        ],
        config=types.GenerateContentConfig(
            tools=[tools_list],
            # Use ANY tool-config to force an actionable tool execution call
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="ANY")
            )
        )
    )

    # Execute calls returned by Gemini
    if response.function_calls:
        for call in response.function_calls:
            if call.name == "move_motor":
                motor_id = int(call.args["motor_id"])
                position = int(call.args["position"])
                
                # Execute on the actual Dynamixel servo
                status = execute_motor_movement(motor_id, position)
                print(f"[RESULT] {status}")
                time.sleep(1.0) # Let the arm finish movement
    else:
        print("Gemini returned a conversational text output instead of a motor tool call.")

finally:
    # --- CLEANUP AND RELEASE TORQUE ---
    print("\nReleasing motors...")
    packetHandler.write1ByteTxRx(portHandler, DXL1_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    packetHandler.write1ByteTxRx(portHandler, DXL2_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    portHandler.closePort()
    print("Session finished safely.")