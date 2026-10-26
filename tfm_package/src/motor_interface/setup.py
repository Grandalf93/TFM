from setuptools import find_packages, setup

package_name = 'motor_interface'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robot',
    maintainer_email='dasanplaen@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'read_position = motor_interface.ReadPosition:main',
            'motor_driver_vel = motor_interface.MotorDriver_Vel:main',           
            'robot_kinematics = motor_interface.DiffRobotKinematics:main',
        ],
    },
)
