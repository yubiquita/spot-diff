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
4. `uv run spot-diff candidates <slug>` — 細かい差分から候補を突出度順に並べ、`work/candidates.png`（左・右・重ね合わせ）を出す。目で確かめて本物を `[[items]]` に書く（`box` は `[x, y, w, h]`、`confidence` は 強/中/弱）。カードの縁など毎回出る偽の候補は `ignore` に矩形で書いて除く
   - 重ね合わせの見方: 赤 = 左にだけある線、シアン = 右にだけある線。片側の色だけなら本物、赤とシアンが対で出るなら位置ずれ（または線の描き直し）
   - `sided` 列は、明るさの差がどれだけ片側に偏っているか（1 = 追加・削除・伸縮、0 = 位置ずれ型）。描き直しも 0 に近くなるので、除外には使わず判定の参考にする
5. `uv run spot-diff candidates <slug> --exclude-known --th 10` — 既知の箇所を除いて、閾値を下げて取りこぼしを探す
6. `uv run spot-diff report <slug>` — `docs/<slug>/` と一覧ページを生成する。そのあと commit と push
