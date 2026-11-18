"""ROS-to-web bridge contract.

The ROS perception node writes an atomic JSON state file and JPEG frame under
/tmp. The Flask app reads those files; it does not create a second camera
capture or publish velocity commands.
"""
