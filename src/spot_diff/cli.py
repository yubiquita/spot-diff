"""spot-diff <analyze|candidates|report|site> [slug]"""
import argparse
import json

import cv2
import numpy as np

from . import align, candidates, diff, report, site
from .puzzle import load


def analyze(pz):
    L, Rw, valid, stats = align.align(pz.photo, pz.meta["left"], pz.meta["right"])
    Rf = diff.refine(L, Rw)
    d = diff.color_diff(L, Rf, valid)
    w = pz.work
    cv2.imwrite(str(w / "L.png"), L)
    cv2.imwrite(str(w / "Rf.png"), Rf)
    cv2.imwrite(str(w / "heat.png"), diff.heatmap(d))
    np.save(w / "d.npy", d)
    (w / "stats.json").write_text(json.dumps(stats))
    print(f"aligned: {stats['inliers']}/{stats['matches']} inliers -> {w}/heat.png")


def show_candidates(pz, th, exclude_known):
    d = np.load(pz.work / "d.npy")
    known = [it["box"] for it in pz.items] if exclude_known else []
    cs = candidates.find(d, th=th, exclude=known)[:20]
    for i, c in enumerate(cs, 1):
        print(f"{i:2d} box={c['box']} mass={c['mass']:.0f} max={c['max']:.0f}")
    L, R = cv2.imread(str(pz.work / "L.png")), cv2.imread(str(pz.work / "Rf.png"))
    out = pz.work / "candidates.png"
    cv2.imwrite(str(out), candidates.sheet(L, R, [c["box"] for c in cs]))
    print(f"-> {out}")


def main():
    ap = argparse.ArgumentParser(prog="spot-diff")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("analyze", "candidates", "report"):
        p = sub.add_parser(name)
        p.add_argument("slug")
        if name == "candidates":
            p.add_argument("--th", type=float, default=20)
            p.add_argument("--exclude-known", action="store_true", help="puzzle.toml の items を除外して再探索")
    sub.add_parser("site")
    a = ap.parse_args()
    if a.cmd == "site":
        print(site.render())
        return
    pz = load(a.slug)
    if a.cmd == "analyze":
        analyze(pz)
    elif a.cmd == "candidates":
        show_candidates(pz, a.th, a.exclude_known)
    elif a.cmd == "report":
        print(report.render(pz))
        print(site.render())
