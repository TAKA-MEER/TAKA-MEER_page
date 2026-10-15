# TAKA-MEER_page

配電盤上部確認用ロボットを開発する「高見舎（タカミヤ、英語表記 TAKA-MEER）」プロジェクトの紹介サイト。
発表会・展示の補足資料として、展示で伝えきれない詳細を来場者が読めるようにするのが目的（スマホ閲覧前提）。
GitHub Pages で一般公開する静的サイト（素の HTML/CSS/JS、ビルドなし）。

運用方針の詳細は [docs/operations.md](docs/operations.md)、ページ構成の計画は [docs/site-plan.md](docs/site-plan.md) を参照。

## ディレクトリ

- `site/` — **公開されるファイルはここだけ**。GitHub Actions がこのフォルダを Pages にデプロイする
- `reference/` — ページ作成用の参考資料（公開リポジトリなので誰でも閲覧可能）
- `reference/private/` — 公開不可の資料。`.gitignore` 済みでコミットされない
- `docs/` — 運用方針・サイト計画などの内部ドキュメント（サイトには出ない）

## ページ構成

- 3段階（概要 → しくみ → 技術詳細）で、階層を下りるほど専門的にする。書き分けのルールは docs/site-plan.md
- ヘッダー・フッター・表示灯（`.depth`）は全ページに同じ形で直書きしている。サイト内リンクを増減するときは全ページのフッターを直す
- リンクは相対パス（下層は `../`）。404.html だけは `/TAKA-MEER_page/` からの絶対パス

## 作業ルール

- 回答・ドキュメント・コミットメッセージは日本語
- サイトに載せる情報は `reference/` の資料を根拠にする。資料にない事実（性能値、所属、人名など）を推測で書かない。不明点はユーザーに確認する
- `reference/private/` の内容は、ユーザーの明示的な許可なく `site/` や `reference/` に転記しない
- 外部ライブラリ・ビルドツールは原則導入しない。導入する場合はユーザーに相談する
- 画像は `site/assets/img/` に置き、公開前に位置情報（EXIF）除去とリサイズを行う（詳細は docs/operations.md）
- Windows（SolidWorks あり）と Ubuntu（ロボット制御ソフトあり）の両方から編集する。OS 依存のスクリプトやパスを書かない。作業前に `git pull`
- SolidWorks 操作は Windows 環境でのみ可能。Ubuntu では `reference/private/` が無い可能性がある
- 変更後は `python -m http.server 8000 -d site`（Ubuntu は `python3`）でローカル確認する
- `main` への push で本番に即反映される。push はユーザーの指示があるときのみ
