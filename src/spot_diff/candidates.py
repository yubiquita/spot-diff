"""List difference blobs and render left/right crops for visual review."""
import cv2
import numpy as np


def find(d, th=20, margin=40, exclude=()):
    d = d.copy()
    d[:margin] = 0; d[-margin:] = 0; d[:, :margin] = 0; d[:, -margin:] = 0
    for x, y, w, h in exclude:
        d[max(0, y - 20):y + h + 20, max(0, x - 20):x + w + 20] = 0
    bw = cv2.morphologyEx((d > th).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    bw = cv2.dilate(bw, np.ones((31, 31), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw)
    out = []
    for i in range(1, n):
        x, y, w, h, _ = st[i]
        sc = d[lab == i]
        out.append({"box": [int(x), int(y), int(w), int(h)], "mass": float(sc[sc > th].sum()), "max": float(sc.max())})
    return sorted(out, key=lambda c: -c["mass"])


def sheet(L, R, boxes, width=1400, row_h=300):
    rows = []
    for i, (x, y, w, h) in enumerate(boxes, 1):
        p = 40
        y0, y1, x0, x1 = max(0, y - p), min(L.shape[0], y + h + p), max(0, x - p), min(L.shape[1], x + w + p)
        a, b = L[y0:y1, x0:x1], R[y0:y1, x0:x1]
        pair = np.hstack([a, np.full((a.shape[0], 10, 3), 255, np.uint8), b])
        s = min(row_h / pair.shape[0], width / pair.shape[1])
        pair = cv2.resize(pair, None, fx=s, fy=s)
        c = np.full((pair.shape[0] + 30, width, 3), 40, np.uint8)
        c[30:, :pair.shape[1]] = pair
        cv2.putText(c, f"{i} box=({x},{y},{w},{h})", (5, 24), 0, 0.8, (0, 255, 255), 2)
        rows.append(c)
    return np.vstack(rows) if rows else np.zeros((10, width, 3), np.uint8)
