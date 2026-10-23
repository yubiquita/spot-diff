"""Crop both pages from the photo and warp the right page onto the left (SIFT + RANSAC)."""
import cv2
import numpy as np


def crop(img, box):
    x0, y0, x1, y1 = box
    return img[y0:y1, x0:x1]


def align(photo, left_box, right_box):
    img = cv2.imread(str(photo))
    L, R = crop(img, left_box), crop(img, right_box)
    sift = cv2.SIFT_create(8000)
    gl, gr = [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) for x in (L, R)]
    kl, dl = sift.detectAndCompute(gl, None)
    kr, dr = sift.detectAndCompute(gr, None)
    m = cv2.BFMatcher().knnMatch(dr, dl, k=2)
    good = [a for a, b in m if a.distance < 0.75 * b.distance]
    src = np.float32([kr[a.queryIdx].pt for a in good])
    dst = np.float32([kl[a.trainIdx].pt for a in good])
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    size = (L.shape[1], L.shape[0])
    Rw = cv2.warpPerspective(R, H, size)
    valid = cv2.warpPerspective(np.full(R.shape[:2], 255, np.uint8), H, size)
    stats = {"matches": len(good), "inliers": int(mask.sum())}
    return L, Rw, valid, stats
