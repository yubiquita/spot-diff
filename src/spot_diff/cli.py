"""spot-diff <analyze|candidates|report|site> [slug]"""
import argparse
import json

import cv2
import numpy as np

from . import align, candidates, diff, report, site
from .puzzle import load


def analyze(pz):
    L, Rw, valid, stats = align.align(pz.photo, pz.meta["left"], pz.meta["right"])
    Rf = diff.refine(L, Rw, **diff.COARSE)
    d = diff.color_diff(L, Rf, valid, **diff.COARSE)
    Rff = diff.refine(L, Rw, **diff.FINE)
    w = pz.work
    cv2.imwrite(str(w / "L.png"), L)
    cv2.imwrite(str(w / "Rf.png"), Rf)
    cv2.imwrite(str(w / "Rff.png"), Rff)
    d_fine = diff.color_diff(L, Rff, valid, **diff.FINE)
    cv2.imwrite(str(w / "heat.png"), diff.heatmap(d))
    cv2.imwrite(str(w / "heat_fine.png"), diff.heatmap(d_fine))
    np.save(w / "d.npy", d)
    np.save(w / "d_fine.npy", d_fine)
    np.save(w / "s_fine.npy", diff.signed_luma(L, Rff, valid, **diff.FINE))
    (w / "stats.json").write_text(json.dumps(stats))
    print(f"aligned: {stats['inliers']}/{stats['matches']} inliers -> {w}/heat.png")


def _overlaps(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def show_candidates(pz, th, exclude_known):
    w = pz.work
    known = [it["box"] for it in pz.items] if exclude_known else []
    cs = candidates.find(np.load(w / "d_fine.npy"), np.load(w / "s_fine.npy"), th=th,
                         exclude=known, ignore=pz.meta.get("ignore", []))[:20]
    for i, c in enumerate(cs, 1):
        tag = next((f"#{k}" for k, it in enumerate(pz.items, 1) if _overlaps(c["box"], it["box"])), "")
        print(f"{i:2d} box={c['box']} peak={c['peak']:.0f} mass={c['mass']:.0f} sided={c['sided']:.2f} {tag}")
    L, R = cv2.imread(str(w / "L.png")), cv2.imread(str(w / "Rff.png"))
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
            p.add_argument("--th", type=float, default=14)
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
