# 運用方針

## 基本方針

| 項目 | 方針 |
|---|---|
| 公開範囲 | 一般公開 |
| ホスティング | GitHub Pages（GitHub Actions でデプロイ） |
| リポジトリ | public（ソース・参考資料も公開される前提） |
| 技術 | 素の HTML / CSS / JS。ビルド工程なし |
| リポジトリURL | https://github.com/TAKA-MEER/TAKA-MEER_page |
| 公開URL | https://taka-meer.github.io/TAKA-MEER_page/ |
| 管理者 | 1名（yisahia787） |
| ブランチ | `main` のみ。push = 本番反映 |
| 作業環境 | Windows と Ubuntu の両方（下記「複数環境での作業」参照） |
| 独自ドメイン | 任意。URL を外部（チラシ・発表資料等）に載せる前に決める |

## 公開してよい情報の基準

リポジトリもサイトも誰でも見られる。迷ったら `reference/private/` に置き、載せない。

**載せない／確認してから載せるもの**

- 現場（設置先の建物・設備）を特定できる写真や名称
- 配電盤内部の詳細な写真、配線図、設備の型番（セキュリティ上の配慮）
- 本人の同意がないメンバーの氏名・顔写真
- 共同研究先・企業との契約上、非公開の情報
- 未発表の論文・特許出願前の技術詳細
- 個人の連絡先（問い合わせ先はプロジェクト用のアドレスかフォームにする）

## ディレクトリの使い分け

```
site/                  公開されるファイル（ここだけがWebに出る）
  index.html
  404.html
  assets/css|js|img/
reference/             参考資料（公開OKのもの）
  private/             公開NGの資料（gitignore、ローカルのみ）
docs/                  運用ドキュメント
.github/workflows/     デプロイ設定
```

`reference/private/` は Git 管理外なので、**作成したPCにしか存在しない**（Windows と Ubuntu の間でも同期されない）。必要なら USB・クラウドストレージ等で個別に共有し、バックアップも取ること。

## 複数環境での作業

| 環境 | 主な役割 |
|---|---|
| Windows | SolidWorks での CAD 画像作成、サイト編集 |
| Ubuntu | ロボット制御ソフト（実機の写真・動画・ログ取得）、サイト編集 |

- **作業開始時に必ず `git pull`、終了時に commit & push**。片方で push し忘れると、もう片方で競合する
- 改行コードは `.gitattributes` で LF に統一済み。エディタは `.editorconfig` に従う（VS Code は EditorConfig 拡張を入れる）
- ファイル名は半角英数字・ハイフンのみ。大文字小文字だけ違うファイル名は作らない（Windows では同じファイル扱いになる）
- CAD 由来の画像は Windows で書き出し、加工後 `site/assets/img/` に置いて push する。Ubuntu 側では pull して使う
- ロボット制御ソフト本体のコードはこのリポジトリに置かない（別リポジトリで管理し、必要ならリンクする）

## 更新フロー

1. `git pull`
2. `reference/` に資料を追加（必要なら）
3. `site/` を編集
4. ローカルで確認
   ```
   python -m http.server 8000 -d site     # Windows
   python3 -m http.server 8000 -d site    # Ubuntu
   ```
   → http://localhost:8000 を開く。スマホ幅（DevTools のデバイスモード）でも確認する
5. コミットして `main` に push
6. GitHub の Actions タブでデプロイ成功を確認（1〜2分）

大きな変更（デザイン刷新など）はブランチを切って作業し、確認後に `main` へマージする。

## 画像・動画のルール

- **位置情報を消す**：スマホ写真は EXIF に GPS 情報が入っている。公開前に必ず除去する
- **サイズ**：横幅は最大 1920px 程度、1枚 500KB 以下を目安。形式は写真なら JPEG / WebP、図なら PNG / SVG
- **ファイル名**：半角英数字・ハイフンのみ（例：`robot-overview-2026-10.jpg`）
- **動画**：リポジトリに直接置かない（GitHub は 100MB 制限、Pages にも容量制限がある）。YouTube 等に上げて埋め込む
- **alt 属性**：すべての画像に内容を説明する alt を付ける
- CAD 画像は SolidWorks からスクリーンショット／エクスポートして使う。元の CAD ファイル（.SLDPRT 等）は置かない

## 独自ドメインを導入する場合

1. ドメインを取得（Cloudflare Registrar、お名前.com など）
2. DNS に GitHub Pages 用のレコードを設定
   - サブドメイン（例 `www.example.com`）：`CNAME` → `taka-meer.github.io`
   - ルートドメイン：`A` レコードを GitHub 指定の4つの IP に向ける
3. GitHub の Settings → Pages → Custom domain に入力し、「Enforce HTTPS」を有効化
4. ドメイン更新期限をカレンダーに登録する（失効すると第三者に取得されるリスクがある）

## 定期的に見直すこと

- 開発進捗セクションの更新（目安：マイルストーンごと）
- リンク切れの確認
- 掲載情報が古くなっていないか（メンバー、所属、連絡先）
