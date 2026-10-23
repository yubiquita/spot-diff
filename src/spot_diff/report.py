"""Render docs/<slug>/index.html (self-contained, images embedded as base64)."""
import base64
import html
import json

import cv2

from .puzzle import DOCS, Puzzle

STYLE = """
body{font-family:system-ui,"Hiragino Sans","Noto Sans JP",sans-serif;margin:0;background:#f6f4ef;color:#222;line-height:1.6}
main{max-width:1100px;margin:auto;padding:16px} h1{font-size:1.5rem} h2{border-left:6px solid #c0392b;padding-left:8px;margin-top:2em}
a{color:#c0392b} .back{font-size:.9rem}
.summary{background:#fff;border-radius:10px;padding:12px 16px;box-shadow:0 1px 3px #0002}
table{border-collapse:collapse;width:100%;background:#fff} td,th{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}
.pair{display:flex;gap:8px;flex-wrap:wrap} .pair figure{flex:1 1 300px;margin:0} img{max-width:100%;border-radius:6px;display:block}
figcaption{font-size:.85rem;color:#666;text-align:center}
.card{background:#fff;border-radius:10px;padding:10px 14px;margin:14px 0;box-shadow:0 1px 3px #0002}
.card h3{margin:.2em 0} .n{display:inline-block;background:#c0392b;color:#fff;border-radius:50%;width:1.6em;text-align:center;margin-right:.4em}
.trio{display:flex;gap:6px;overflow-x:auto} .trio figure{margin:0;flex:0 0 auto} .trio img{height:200px;width:auto;max-width:none}
.conf{font-size:.75rem;padding:2px 8px;border-radius:10px;margin-left:.5em;vertical-align:middle}
.c強{color:#1e7b34} .c中{color:#b9770e} .c弱{color:#7f8c8d} span.c強{background:#e3f4e7} span.c中{background:#fdf2dc} span.c弱{background:#eceff0}
"""


def b64(img, q=82):
    return base64.b64encode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])[1]).decode()


def annotate(img, items, scale=0.5):
    o = img.copy()
    for i, it in enumerate(items, 1):
        x, y, w, h = it["box"]
        p = 18
        cv2.rectangle(o, (x - p, y - p), (x + w + p, y + h + p), (0, 0, 255), 6)
        cx, cy = max(x - p, 40), max(y - p, 40)
        cv2.circle(o, (cx, cy), 34, (0, 0, 255), -1)
        cv2.putText(o, str(i), (cx - 14 if i < 10 else cx - 26, cy + 15), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 4)
    return cv2.resize(o, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)


def card(i, it, L, R, heat):
    x, y, w, h = it["box"]
    p = max(40, int(0.35 * max(w, h)))
    y0, y1, x0, x1 = max(0, y - p), min(L.shape[0], y + h + p), max(0, x - p), min(L.shape[1], x + w + p)
    s = 260 / (y1 - y0)
    a, b, hm = [cv2.resize(z[y0:y1, x0:x1], None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC) for z in (L, R, heat)]
    conf = html.escape(it["confidence"])
    figs = "".join(f'<figure><img src="data:image/jpeg;base64,{b64(z)}"><figcaption>{c}</figcaption></figure>'
                   for z, c in ((a, "左"), (b, "右（位置合わせ後）"), (hm, "差分")))
    return (f'<div class="card"><h3><span class="n">{i}</span>{html.escape(it["where"])}'
            f' <span class="conf c{conf}">確度 {conf}</span></h3><p>{html.escape(it["what"])}</p><div class="trio">{figs}</div></div>')


def render(pz: Puzzle):
    m, items = pz.meta, pz.items
    L, R, heat = (cv2.imread(str(pz.work / f)) for f in ("L.png", "Rf.png", "heat.png"))
    stats = json.loads((pz.work / "stats.json").read_text())
    title = html.escape(m["title"])
    found = f"{m['total']}個中{len(items)}個を検出" if len(items) < m["total"] else f"{m['total']}個すべて検出"
    summary = "<br>".join(html.escape(s) for s in m.get("summary", "").strip().splitlines())
    rows = "".join(f"<tr><td>{i}</td><td>{html.escape(it['where'])}</td><td>{html.escape(it['what'])}</td>"
                   f"<td class='c{html.escape(it['confidence'])}'>{html.escape(it['confidence'])}</td></tr>"
                   for i, it in enumerate(items, 1))
    cards = "".join(card(i, it, L, R, heat) for i, it in enumerate(items, 1))
    doc = f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} 画像処理レポート</title><style>{STYLE}</style><main>
<p class="back"><a href="../">← 一覧へ</a></p>
<h1>{title} 画像処理レポート</h1>
<p>{html.escape(str(m.get("date", "")))} ・ {html.escape(m.get("place", ""))}</p>
<div class="summary"><b>結果: {found}。</b><br>{summary}</div>

<h2>一覧</h2><table><tr><th>#</th><th>場所</th><th>違い</th><th>確度</th></tr>{rows}</table>

<h2>全体図（赤枠 = 検出箇所）</h2>
<div class="pair"><figure><img src="data:image/jpeg;base64,{b64(annotate(L, items))}"><figcaption>左ページ</figcaption></figure>
<figure><img src="data:image/jpeg;base64,{b64(annotate(R, items))}"><figcaption>右ページ（左に重なるよう変形済み）</figcaption></figure></div>
<h2>差分マップ</h2><figure style="max-width:640px;margin:auto"><img src="data:image/jpeg;base64,{b64(cv2.resize(heat, None, fx=.5, fy=.5))}"><figcaption>明るいほど色の差が大きい（縁の帯はカードの端と照明の影響）</figcaption></figure>

<h2>各差分の拡大</h2>{cards}

<h2>手法</h2><ol>
<li>写真から左右のページを切り出す</li>
<li>SIFT 特徴点のマッチング（RANSAC で {stats["inliers"]:,} 点が一致）からホモグラフィを求め、右ページを左ページに重ねる</li>
<li>カードのたわみを補正する: Farneback オプティカルフローを強くぼかした低周波成分だけで微修正（本物の差分まで消さないように）</li>
<li>Lab 色空間で色差を計算。照明ムラは大きなスケールの平均を引いて補正し、±3px の近傍の最小値をとって残りのずれを吸収する</li>
<li>閾値処理と連結成分で候補を抽出し、既知の箇所をマスクして閾値を下げて再探索する</li>
<li>全候補を拡大して目視で判定する（ノイズ・汚れ・縁は除外）</li></ol>
<p class="back"><a href="https://github.com/yubiquita/spot-diff">ソースコード</a></p>
</main></html>'''
    out = DOCS / pz.slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(doc)
    thumb = annotate(L, items, scale=360 / L.shape[1])
    cv2.imwrite(str(out / "thumb.jpg"), thumb, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return out / "index.html"
