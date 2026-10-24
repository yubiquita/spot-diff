"""Absorb card bending with low-frequency optical flow, then compute difference maps.

Two passes:
- coarse: heavy smoothing and ±3px tolerance — robust, catches large changes
- fine:   lighter smoothing and ±2px tolerance — catches thin-line changes (e.g. a stroke a few px longer)
"""
import cv2
import numpy as np

COARSE = dict(flow_pre=3, flow_win=151, flow_post=40, blur=2.0, tol=3, illum=60)
FINE = dict(flow_pre=2, flow_win=61, flow_post=15, blur=1.2, tol=2, illum=40)


def refine(L, Rw, flow_pre, flow_win, flow_post, **_):
    gl = cv2.cvtColor(L, cv2.COLOR_BGR2GRAY)
    gr = cv2.cvtColor(Rw, cv2.COLOR_BGR2GRAY)
    # flow is smoothed so real differences are not "warped away"
    flow = cv2.calcOpticalFlowFarneback(cv2.GaussianBlur(gl, (0, 0), flow_pre), cv2.GaussianBlur(gr, (0, 0), flow_pre),
                                        None, 0.5, 5, flow_win, 3, 7, 1.5, 0)
    flow = cv2.GaussianBlur(flow, (0, 0), flow_post)
    h, w = gl.shape
    gx, gy = np.meshgrid(np.arange(w), np.arange(h))
    return cv2.remap(Rw, (gx + flow[..., 0]).astype(np.float32), (gy + flow[..., 1]).astype(np.float32),
                     cv2.INTER_LINEAR)


def _lab_pair(L, Rf, blur, illum):
    lab = lambda x: cv2.cvtColor(cv2.GaussianBlur(x, (0, 0), blur), cv2.COLOR_BGR2LAB).astype(np.float32)
    a, b = lab(L), lab(Rf)
    # illumination: match large-scale mean per channel
    for c in range(3):
        b[..., c] += cv2.GaussianBlur(a[..., c], (0, 0), illum) - cv2.GaussianBlur(b[..., c], (0, 0), illum)
    return a, b


def _mask_invalid(d, valid, edge=15):
    d[valid < 255] = 0
    d[:edge] = 0; d[-edge:] = 0; d[:, :edge] = 0; d[:, -edge:] = 0
    return d


def color_diff(L, Rf, valid, blur, tol, illum, **_):
    h, w = L.shape[:2]
    a, b = _lab_pair(L, Rf, blur, illum)
    # min over a small neighborhood to suppress residual misalignment
    d = np.full((h, w), np.inf, np.float32)
    for dx in (-tol, 0, tol):
        for dy in (-tol, 0, tol):
            bs = cv2.warpAffine(b, np.float32([[1, 0, dx], [0, 1, dy]]), (w, h), borderMode=cv2.BORDER_REPLICATE)
            d = np.minimum(d, np.sqrt(((a - bs) ** 2).sum(2)))
    return _mask_invalid(d, valid)


def signed_luma(L, Rf, valid, blur, illum, **_):
    """L* (left) - L* (right). Misalignment leaves +/- pairs across an edge; a real change is one-signed."""
    a, b = _lab_pair(L, Rf, blur, illum)
    return _mask_invalid(a[..., 0] - b[..., 0], valid)


def heatmap(d):
    return cv2.applyColorMap(np.clip(d * 4, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
