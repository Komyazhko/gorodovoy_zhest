import numpy as np
from vision.depth_estimator import estimate_depth_m

def test_median_depth():
    img = np.full((20, 20), 1500, dtype=np.uint16)
    assert estimate_depth_m(img, 10, 10, 0.001) == 1.5

def test_zero_depth_invalid():
    assert estimate_depth_m(np.zeros((20,20), dtype=np.uint16), 10, 10) is None
