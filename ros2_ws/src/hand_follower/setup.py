from setuptools import setup
package_name = 'hand_follower'
setup(
    name=package_name, version='0.1.0', packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'], zip_safe=True,
    maintainer='Project Maintainer',
    maintainer_email='maintainer@example.com',
    description='Safe hand target follower', license='Apache-2.0',
    entry_points={'console_scripts': [
        'follower_node = hand_follower.follower_node:main',
    ]},
)
