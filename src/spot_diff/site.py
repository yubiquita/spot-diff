"""Render docs/index.html listing all puzzles."""
import html

from .puzzle import DOCS, all_puzzles
from .report import STYLE, found

GRID = """
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.grid a{display:block;background:#fff;border-radius:10px;padding:10px;box-shadow:0 1px 3px #0002;color:inherit;text-decoration:none}
.grid h3{margin:.4em 0 .1em;font-size:1rem} .grid p{margin:0;font-size:.85rem;color:#666}
"""


def render():
    cards = []
    for pz in all_puzzles():
        m = pz.meta
        if not (DOCS / pz.slug / "index.html").exists():
            continue
        cards.append(f'<a href="{pz.slug}/"><img src="{pz.slug}/thumb.jpg" alt="" loading="lazy">'
                     f'<h3>{html.escape(m["title"])}</h3>'
                     f'<p>{html.escape(str(m.get("date", "")))} ・ {found(m["total"], len(pz.items))}</p></a>')
    doc = f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>間違い探しを画像処理で解く</title><style>{STYLE}{GRID}</style><main>
<h1>間違い探しを画像処理で解く</h1>
<p>2枚の絵を特徴点マッチングで重ね合わせて色の差分をとり、間違いを探した記録です。</p>
<div class="grid">{"".join(cards)}</div>
<p class="back"><a href="https://github.com/yubiquita/spot-diff">ソースコード</a></p>
</main></html>'''
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").touch()
    (DOCS / "index.html").write_text(doc)
    return DOCS / "index.html"
