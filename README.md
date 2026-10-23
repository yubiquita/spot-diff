# spot-diff

間違い探しを画像処理で解く。公開ページ: https://yubiquita.github.io/spot-diff/

## 構成

- `puzzles/<slug>/photo.jpg` — 入力写真（EXIF は除去して置く）
- `puzzles/<slug>/puzzle.toml` — タイトル・切り出し範囲・判定結果
- `puzzles/<slug>/work/` — 中間ファイル（git 管理外）
- `docs/` — GitHub Pages（`docs/index.html` が一覧、`docs/<slug>/index.html` が各レポート）
- `src/spot_diff/` — 処理本体（align → diff → candidates → report / site）

## 新しい間違い探しを追加する

1. `puzzles/<slug>/` を作る（slug は例えば `2026-11-xxx`）。`photo.jpg` を置き、EXIF を除去する
2. `puzzle.toml` に `title` / `date` / `place` / `total` と、左右ページの切り出し矩形 `left` / `right`（写真のピクセル座標 `[x0, y0, x1, y1]`）を書く
3. `uv run spot-diff analyze <slug>` — 位置合わせして差分マップ `work/heat.png` を作る
4. `uv run spot-diff candidates <slug>` — 候補を一覧し、左右を並べた `work/candidates.png` を出す。目で確かめて本物を `[[items]]` に書く（`box` は `[x, y, w, h]`、`confidence` は 強/中/弱）
5. `uv run spot-diff candidates <slug> --exclude-known --th 12` — 既知の箇所を除いて、閾値を下げて取りこぼしを探す
6. `uv run spot-diff report <slug>` — `docs/<slug>/` と一覧ページを生成する。そのあと commit と push
