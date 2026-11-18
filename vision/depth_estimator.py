import numpy as np


def median_depth_m(depth_image, encoding, scale=0.001,
                   min_depth=0.25, max_depth=5.0):
    values = np.asarray(depth_image, dtype=np.float32)
    if encoding in ('16UC1', 'mono16'):
        values *= float(scale)
    elif encoding != '32FC1':
        return None
    valid = values[np.isfinite(values) & (values >= min_depth) & (values <= max_depth)]
    if valid.size < 8:
        return None
    return float(np.median(valid))
