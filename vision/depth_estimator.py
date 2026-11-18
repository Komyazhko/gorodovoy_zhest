import numpy as np

def estimate_depth_m(depth_image, center_x, center_y, depth_scale=0.001,
                     radius=5, min_depth=0.25, max_depth=5.0):
    if depth_image is None or depth_image.ndim != 2:
        return None
    h, w = depth_image.shape
    x, y = int(center_x), int(center_y)
    roi = depth_image[max(0,y-radius):min(h,y+radius+1),
                      max(0,x-radius):min(w,x+radius+1)].astype(np.float32)
    valid = roi[np.isfinite(roi) & (roi > 0)]
    if valid.size == 0:
        return None
    distance = float(np.median(valid)) * float(depth_scale)
    return distance if min_depth <= distance <= max_depth else None
