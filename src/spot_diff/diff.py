"""Absorb card bending with low-frequency optical flow, then compute a Lab color-difference map."""
import cv2
import numpy as np


def refine(L, Rw):
    gl = cv2.cvtColor(L, cv2.COLOR_BGR2GRAY)
    gr = cv2.cvtColor(Rw, cv2.COLOR_BGR2GRAY)
    # heavy blur so real differences are not "warped away"
    flow = cv2.calcOpticalFlowFarneback(cv2.GaussianBlur(gl, (0, 0), 3), cv2.GaussianBlur(gr, (0, 0), 3),
                                        None, 0.5, 5, 151, 3, 7, 1.5, 0)
    flow = cv2.GaussianBlur(flow, (0, 0), 40)
    h, w = gl.shape
    gx, gy = np.meshgrid(np.arange(w), np.arange(h))
    return cv2.remap(Rw, (gx + flow[..., 0]).astype(np.float32), (gy + flow[..., 1]).astype(np.float32),
                     cv2.INTER_LINEAR)


def color_diff(L, Rf, valid, tol=3, edge=15):
    h, w = L.shape[:2]
    lab = lambda x: cv2.cvtColor(cv2.GaussianBlur(x, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    a, b = lab(L), lab(Rf)
    # illumination: match large-scale mean per channel
    for c in range(3):
        b[..., c] += cv2.GaussianBlur(a[..., c], (0, 0), 60) - cv2.GaussianBlur(b[..., c], (0, 0), 60)
    # min over a small neighborhood to suppress residual misalignment
    d = np.full((h, w), np.inf, np.float32)
    for dx in (-tol, 0, tol):
        for dy in (-tol, 0, tol):
            bs = cv2.warpAffine(b, np.float32([[1, 0, dx], [0, 1, dy]]), (w, h), borderMode=cv2.BORDER_REPLICATE)
            d = np.minimum(d, np.sqrt(((a - bs) ** 2).sum(2)))
    d[valid < 255] = 0
    d[:edge] = 0; d[-edge:] = 0; d[:, :edge] = 0; d[:, -edge:] = 0
    return d


def heatmap(d):
    return cv2.applyColorMap(np.clip(d * 4, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
