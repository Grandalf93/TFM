import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():


    # 1. Nodes from motor_interface package
    read_position_node = Node(
        package='motor_interface',
        executable='read_position',   # <-- Change to your executable name
        name='controller_input',
        output='screen'
    )

    kinematics_node = Node(
        package='motor_interface',
        executable='robot_kinematics',   # <-- Change to your executable name
        name='differential_kinematics'
        #, output='screen'
    )

    motor_node = Node(
        package='motor_interface',
        executable='motor_driver_vel',   # <-- Change to your executable name
        name='dynamixel_velocity_driver'
        #, output='screen'
    )


    delayed_position_node = TimerAction(
        period=3.0,  # Delay in seconds
        actions=[read_position_node]
    )


    # 2. Include the launch file from rplidar_ros
    rplidar_share_dir = get_package_share_directory('rplidar_ros')
    # Locate the launch file (change rplidar_a1_launch.py to match your LIDAR model if necessary)
    rplidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rplidar_share_dir, 'launch', 'rplidar_a1_launch.py')
        )
    )

    return LaunchDescription([        
        kinematics_node,
        motor_node,
        #rplidar_launch
    ])