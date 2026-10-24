"""Rank difference blobs on the fine map and render left/right/overlay crops for visual review."""
import cv2
import numpy as np


def _blank(d, margin, boxes, pad=0):
    d[:margin] = 0; d[-margin:] = 0; d[:, :margin] = 0; d[:, -margin:] = 0
    for x, y, w, h in boxes:
        d[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 0
    return d


def find(d, s, th=14, margin=40, exclude=(), ignore=()):
    """Blobs ranked by prominence (peak above the local background), not by total mass,
    so a thin stroke a few px longer ranks alongside large color changes.

    sided: 1 = one-signed luminance change (stroke added/removed/extended),
           0 = balanced +/- pair (shifted edge: misalignment, or a line redrawn elsewhere).
    """
    d = _blank(_blank(d.copy(), margin, ignore), margin, exclude, pad=20)
    r = np.clip(d - cv2.GaussianBlur(d, (0, 0), 20), 0, None)
    core = cv2.morphologyEx((r > th).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(core, np.ones((31, 31), np.uint8)))
    out = []
    for i in range(1, n):
        x, y, w, h, _ = st[i]
        reg = lab == i
        sc, v = r[reg], s[reg & (core > 0)]
        pos, neg = v[v > 0].sum(), -v[v < 0].sum()
        out.append({"box": [int(x), int(y), int(w), int(h)], "peak": float(sc.max()),
                    "mass": float(sc[sc > th].sum()), "sided": float(abs(pos - neg) / (pos + neg + 1e-6))})
    return sorted(out, key=lambda c: -c["peak"])


def overlay(a, b):
    """Red = ink only on the left, cyan = ink only on the right, gray = same."""
    ga, gb = (cv2.cvtColor(z, cv2.COLOR_BGR2GRAY) for z in (a, b))
    return cv2.merge([ga, ga, gb])


def sheet(L, R, boxes, width=1400, row_h=260):
    rows = []
    for i, (x, y, w, h) in enumerate(boxes, 1):
        p = 40
        y0, y1, x0, x1 = max(0, y - p), min(L.shape[0], y + h + p), max(0, x - p), min(L.shape[1], x + w + p)
        a, b = L[y0:y1, x0:x1], R[y0:y1, x0:x1]
        gap = np.full((a.shape[0], 10, 3), 255, np.uint8)
        row = np.hstack([a, gap, b, gap, overlay(a, b)])
        s = min(row_h / row.shape[0], width / row.shape[1])
        row = cv2.resize(row, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        c = np.full((row.shape[0] + 30, width, 3), 40, np.uint8)
        c[30:, :row.shape[1]] = row
        cv2.putText(c, f"{i} box=({x},{y},{w},{h})", (5, 24), 0, 0.8, (0, 255, 255), 2)
        rows.append(c)
    return np.vstack(rows) if rows else np.zeros((10, width, 3), np.uint8)
