# 袋井ライフハック 横展開 設計指示書

- 版：v1.0（2026-07-02）
- 対象：fukuroi.enshu-lifehack.com（袋井ライフハック）新設
- 基準：磐田ライフハック（iwata.enshu-lifehack.com／リポジトリ enshu-lifehack-iwata）2026-07-02時点の完成形
- 前提：磐田側は部品化（parts/＋inject_parts.py）・CSS外部化（assets/site.css）・リンク死活監視（scripts/check_official_links.py）・スクレイピング対策（robots.txt／利用規約／Cloudflare Bot設定）まで完了済み

---

## 0. 目的と確定設計（再確認）

遠州9市町（磐田・袋井・森町・掛川・菊川・御前崎・湖西・浜松3区）への横展開の第1号として袋井版を構築する。確定済みの設計原則は以下のとおりであり、本指示書はこれに従う。

1. 市ごとに**独立リポジトリ・独立Cloudflare Pagesプロジェクト**とする
2. 大項目・中項目の**背骨は全市共通**とし、中項目は**三層管理**（①全市共通／②汎用追加／③市固有）とする
3. 市ごとの差分は**市プロファイル（city.json）**に集約する
4. CV導線は市により差別化する：**介護CVリードは磐田・袋井・森町のみ**。構造リンク（フッター等）と本文中の文脈リンクは全市共通。不動産・磐田物語への導線は全市共通
5. ボトルネックは**人力のデータ検証**であり、AIトークンではない。したがって設計の中心は「検証待ち行列の管理」と「未検証ページを公開しない仕組み」に置く

袋井はCV観点で最重要の市である（介護CVあり・磐田隣接・不動産商圏内）。第1号としてここで確立した手順が残り7市町のテンプレートになる。

---

## 1. 全体アーキテクチャ

```
enshu-lifehack-iwata   (既存)  → iwata.enshu-lifehack.com
enshu-lifehack-fukuroi (新設)  → fukuroi.enshu-lifehack.com
        │
        ├─ 磐田リポジトリから複製する共通資産
        │    parts/（footer/header/disclaimer/head-css）
        │    assets/site.css
        │    scripts/（inject_parts.py / check_official_links.py /
        │              build-search-index.mjs / check-synonyms.mjs / test-search.mjs）
        │    404.html / robots.txt / _redirects / wrangler.toml / .assetsignore
        │    terms/（利用規約。市名等を差し替え）
        │
        ├─ 市プロファイルで差し替える資産
        │    data/city.json（新設・本指示書§4）
        │    data/topics_master.json（袋井版・本指示書§5）
        │
        └─ 生成する資産
             index.html / life/13カテゴリハブ / 中項目詳細ページ群
             search-index.json / sitemap.xml
```

共通資産の共有方式は、当面「**磐田からのコピー＋市名置換**」とする。サブモジュールや共通リポジトリ化は3市目（森町）着手時に、実際に発生した同期作業量を見てから判断する。2市の間は手作業同期で十分であり、早すぎる抽象化は避ける。ただし将来の統合に備え、**共通資産には市固有の値をハードコードしない**（市名・ドメイン・電話番号等はcity.jsonから注入する）ことを本指示書全体の規約とする。

---

## 2. GitHub初期設定

### 2.1 リポジトリ作成

- リポジトリ名：`enshu-lifehack-fukuroi`（オーナー：iwata-monogatari。組織名は磐田由来だが、リネームはリスクに見合わないため現状維持とする）
- 可視性：Public（磐田と同様。Cloudflare Workers Buildsの接続が容易）
- 作成方法：磐田リポジトリを「Use this template」ではなく**手動クローン→履歴を切って新規リポジトリとしてpush**する。磐田のコミット履歴（重説等の無関係な文脈を含まないことは確認済みだが）を持ち込まないため。

```
git clone https://github.com/iwata-monogatari/enshu-lifehack-iwata.git enshu-lifehack-fukuroi
cd enshu-lifehack-fukuroi
rm -rf .git
git init && git add -A && git commit -m "初期コミット：磐田版v2026-07-02をベースに袋井版を開始"
# GitHub上で enshu-lifehack-fukuroi を空リポジトリとして作成した後
git remote add origin https://github.com/iwata-monogatari/enshu-lifehack-fukuroi.git
git push -u origin main
```

### 2.2 初期コミット直後に行う「磐田剥がし」

複製直後のリポジトリは磐田の実データを全て含む。**磐田固有物の除去を最初の独立コミットとして行い、以後の袋井作業と混ぜない**こと。

| 対象 | 処理 |
|---|---|
| `life/` 配下の全詳細ページ | 削除（袋井版は生成パイプラインで作り直す。磐田本文の流用は誤情報混入の温床になるため**本文の直接コピーは禁止**） |
| `index.html`／カテゴリハブ13枚 | 骨格は残し、市名・リンク・件数をプレースホルダ化（§6の生成対象） |
| `data/topics_master.json` | 袋井版の台帳として初期化（§5.2） |
| `search-index.json`／`sitemap.xml` | 空で初期化（生成物） |
| `robots.txt` | Sitemap行のドメインを fukuroi. に変更。AI学習クローラー12種の拒否リストはそのまま維持 |
| `terms/index.html` | サイト名・URL・制定日を袋井版に差し替え。運営者（富士ヶ丘サービス株式会社）は共通 |
| `reports/`・`docs/` | 磐田の検査レポートを削除 |
| `parts/footer.html` | 市名依存部分をcity.json注入に変更（§4.3） |

**置換保護リスト（2026-07-03追記）**：「磐田→袋井」等の市名一括置換を行う際、以下は**置換対象から除外**すること（過剰置換で運営会社の実所在地まで書き換わる事故が発生したため）。掛川以降の派生でも必ず適用する。

- `磐田物語`（磐田の地域史サイト名。全市共通の相互リンク文脈）
- `富士ヶ丘`／`富士ヶ丘サービス株式会社`（運営会社名。全市共通）
- `iwata-monogatari`（GitHub組織名・リポジトリ名）
- `磐田ライフハック`（相互リンク文脈で意図的に残す）
- `静岡県磐田市見付5789番地1`（運営会社の実所在地。**磐田市**が正しく、進出先の市に書き換えてはならない）

### 2.3 ブランチ・コミット規約

main直コミット、コミットメッセージは日本語とする。**pushは確認不要・Claude Codeの判断でコミット後そのままpushしてよい**（2026-07-02改訂：従来は「公開に影響する変更はpush前に大石が確認」としていたが、machine-verified運用の定着に伴いこの事前確認ゲートは廃止した）。

**デプロイについて（2026-07-03追記）**：本サイトはGitHub連携のWorkers Builds自動デプロイではなく、`npx wrangler deploy`による手動デプロイ方式で運用されている（初回デプロイもwranglerコマンドで行われた）。したがって`git push`だけでは本番（https://fukuroi.enshu-lifehack.com/）に反映されない。ページ生成・修正作業の一連の流れの中で、コミット・push後に`npx wrangler deploy`も確認なしで実行し、本番反映まで完了させること。

---

## 3. Cloudflare初期設定

### 3.1 Pagesプロジェクト（Workers Builds）

1. Cloudflareダッシュボード → Workers & Pages → Create → Pages → Connect to Git
2. リポジトリ `enshu-lifehack-fukuroi` を接続
3. ビルド設定：フレームワークなし（静的）、ビルドコマンド空欄、出力ディレクトリ `/`（磐田と同一。`wrangler.toml`・`.assetsignore` を複製済みのため parts/ reports/ docs/ .github/ は配信から除外される）
4. 初回デプロイで `enshu-lifehack-fukuroi.pages.dev` が発行されることを確認

### 3.2 カスタムドメイン

1. Pagesプロジェクト → Custom domains → `fukuroi.enshu-lifehack.com` を追加
2. `enshu-lifehack.com` ゾーンは既にCloudflare管理下のため、CNAMEレコードは自動作成される。DNSタブで `fukuroi` のCNAME（Proxied・オレンジ雲）を確認
3. HTTPS証明書の発行（数分）を待ち、`https://fukuroi.enshu-lifehack.com/` の200応答を確認

### 3.3 セキュリティ設定の継承確認（作業不要・確認のみ）

磐田で設定済みの以下は**すべて enshu-lifehack.com ゾーン単位の設定**であり、袋井サブドメインに自動適用される。新規設定は不要だが、公開時に以下を確認する。

- Bot Fight Mode：ON（ゾーン全体）
- AI bot policies：Training=Block／Search=Allow／Agent=Allow（ゾーン全体）
- Rate Limiting「block-bulk-copy-50req-per-10s」：対象が「ゾーン全体」であることを確認（無料枠1ルールを全市で共用する設計。市別ルールは作らない）

### 3.4 アクセス解析

磐田と同様にCloudflare Web Analyticsを使用する。**2026-07-03確認：`enshu-lifehack.com`ゾーン単位でRUM（Real User Measurements）が既に「Enable, excluding visitor data in the EU」で有効化済みであり、サブドメインである`fukuroi.enshu-lifehack.com`も自動的にカバーされることを確認した。** サイト個別のJSスニペット設置・`parts/analytics.html`の作成は不要（Cloudflareがプロキシ経由のリクエストへ自動でビーコンを注入する方式のため）。当初想定していた「市ごとに個別サイト登録してトークン管理」は不要と判明。KVは使わない（磐田での障害教訓）。

---

## 4. 市プロファイル（data/city.json）

### 4.1 目的

市ごとの差分を1ファイルに集約し、生成スクリプト・parts注入・フッターがすべてここを参照する。**HTMLやスクリプトに市名・電話番号・URLを直書きすることを禁止**する規約の受け皿。

### 4.2 袋井版の初期値

```json
{
  "city_id": "fukuroi",
  "city_name": "袋井市",
  "site_name": "袋井ライフハック",
  "site_url": "https://fukuroi.enshu-lifehack.com",
  "official": {
    "domain": "www.city.fukuroi.shizuoka.jp",
    "top": "https://www.city.fukuroi.shizuoka.jp/",
    "hall_name": "袋井市役所",
    "hall_address": "〒437-8666 静岡県袋井市新屋1-1-1",
    "hall_tel": "0538-43-2111",
    "branches": [
      { "name": "浅羽支所", "note": "各種届出・証明書は本庁・浅羽支所のどちらでも受付（一部業務を除く）" }
    ],
    "tetsuduki_navi": "https://fukuroi-city.supportnavi.jp/",
    "fire_emergency": "袋井市森町広域行政組合（消防・救急は森町と共同運営）"
  },
  "cv": {
    "kaigo_lead": true,
    "fudosan_link": true,
    "monogatari_link": true,
    "context_links": true
  },
  "notes": [
    "高齢化率は県内低位・人口増加傾向の若い市。子育て・教育カテゴリの需要が磐田より相対的に高い可能性",
    "住まい相談の市公式窓口として「ふくろいすまいの相談センター」が存在（家・住まいカテゴリで要調査）"
  ]
}
```

### 4.3 partsへの反映

`inject_parts.py` を拡張し、parts内の `{{city_name}}` `{{hall_tel}}` 等のプレースホルダをcity.jsonの値で置換してから各HTMLへ注入する方式とする。フッターの遠州ネットワーク欄は「運用中：磐田・袋井／近日運用予定：森町ほか」に更新し、**磐田リポジトリ側のparts/footer.htmlにも同じ更新を入れて両サイトの表記を揃える**（磐田側はparts修正→inject→pushの3手で完了する。部品化の成果を最初に享受する場面）。

---

## 5. 袋井市役所からの情報取得方法

### 5.1 基本方針：スクレイピングではなく「台帳駆動の出典調査」

本サイトの本文は編集方針に基づくオリジナル文章であり、市サイトの転載ではない。取得するのは（a）各中項目に対応する**公式ページのURL**、（b）窓口名・電話・受付時間等の**検証可能な事実**のみ。よって機械的な一括スクレイピングは行わず、**中項目1件ずつの出典調査**として実施する。これは磐田で確立した「公式窓口・確認先」セクションの思想の継承である。

市サイトへのアクセスはリンク死活監視と同じ礼法に従う：リクエスト間隔0.5秒以上、User-Agent明示、深夜大量アクセスをしない。相手は行政サイトであり、こちらが袋井市民の利便に資する紹介サイトである関係を損なわないこと。

### 5.2 台帳：topics_master.json の袋井版スキーマ

磐田の実績（155項目・13カテゴリ）を出発点とし、以下のフィールドを追加した袋井版台帳を作る。**この台帳が生成・検証・公開のすべてを駆動する単一のマスター**である。

```json
{
  "href": "/life/parents-care/find-nursing-home/",
  "icon": "🏠",
  "title": "（袋井版の見出し。磐田版を参考にしつつ袋井の実情で書き直す）",
  "category": "親のこと",
  "synonyms": ["…"],
  "tier": "common",
  "source_iwata": "https://www.city.iwata.shizuoka.jp/…",
  "sources_fukuroi": [
    { "url": "https://www.city.fukuroi.shizuoka.jp/…", "label": "袋井市 高齢者福祉…" }
  ],
  "facts": { "window": "…課", "tel": "0538-…", "hours": "…" },
  "status": "draft",
  "verified_date": null,
  "verified_by": null
}
```

- `tier`：`common`（全市共通155項目由来）／`generic-add`（汎用追加）／`city-only`（袋井固有）の三層
- `status`：`draft`（未着手）→ `ai-checked`（AIが出典URL・事実を収集済み）→ `human-verified`（大石が公式ページと突合済み）→ `published`。**human-verified未満のページは生成しても公開ディレクトリに置かない**（§6.3）
- `verified_date` が磐田で実装済みの「最終確認日」表示の供給源になる

### 5.3 中項目ソース対応表の作成手順（最初の実務）

横展開の確定手順どおり、**磐田155項目の棚卸し→対応表の袋井列埋め**から始める。

1. **磐田列の自動抽出**：磐田リポジトリの各詳細ページ「公式窓口・確認先」セクションから磐田市公式URL（実績2,377リンク・ユニーク377本）を項目別に抽出し、`source_iwata` に格納するスクリプトを作る（機械作業・半日）
2. **袋井列のAI下調べ**：項目ごとに袋井公式サイト内の対応ページを調査し `sources_fukuroi` 候補と `facts` を埋める。調査の優先経路は次の順とする
   - 袋井市公式サイトのサイト内検索・カテゴリ導線（URLは `/kurashi_tetsuzuki/…` 系で磐田と同系統CMSのため、磐田URLのパス構造が探索のヒントになる）
   - 手続きナビ（fukuroi-city.supportnavi.jp）：引越し・結婚・出産・死亡等のライフイベント系の入口として有効
   - 静岡県・国の制度ページ（磐田版で県・国リンクを使っている項目は原則同一URLを流用可）
   - この段階の成果物は `status: ai-checked` であり、**公開物ではない**
3. **対応不能項目の仕分け**：袋井に対応制度・窓口がない項目は `tier` を見直すか対象外フラグを付ける。逆に袋井固有項目（例：浅羽支所での手続き、ふくろいすまいの相談センター、袋井市森町広域行政組合の消防救急、メローねっと等）を `city-only` として追加起票する
4. **人力検証**：大石が `ai-checked` の項目を公式ページと突合し、`human-verified`＋`verified_date` を付す。**1項目あたり2〜3分×155項目≒6〜8時間が本プロジェクトの真のクリティカルパス**。検証はカテゴリ単位でまとめて行い、§7の段階公開と同期させる

### 5.4 検証キューの見える化

`scripts/report_status.py` を新設し、台帳のstatus集計（draft/ai-checked/human-verified/published別、カテゴリ別）を1コマンドで表示できるようにする。日々の「今日はどのカテゴリを検証するか」の判断材料であり、ボトルネック管理の計器盤である。

---

## 6. 生成パイプライン

### 6.1 生成スクリプト（scripts/generate_pages.py 新設）

- 入力：`data/topics_master.json`＋`data/city.json`＋テンプレート（磐田の新世代詳細ページ構造を正とする：H1→本文セクション→Q&A→タイプ別タブ→今日動けること→公式窓口・確認先→関連リンク→CVブロック→解決確認）
- 出力：`life/<category>/<slug>/index.html`
- 本文はAI執筆（磐田の編集トーンを踏襲：市民目線・非公式明示・必ず公式へ誘導・押し売りしない）。**磐田版本文の機械置換（磐田→袋井の文字列置換）は禁止**。制度の細部が市で異なるため、置換流用は誤情報の量産になる
- CVブロックはcity.jsonの `cv` フラグで出し分ける（袋井は kaigo_lead=true なので磐田と同構成）
- 生成後に `inject_parts.py` を必ず実行し、部品とプレースホルダを確定させる

### 6.2 検査スクリプト（磐田資産を流用・拡張）

公開前検査を1コマンド（`scripts/inspect_all.py`）に束ねる。中身は磐田で実証済みの検査の自動化である。

1. 空`<style>`・site.css読込・bodyクラスの全数検査（磐田の5ページ事故の再発防止）
2. タブ既定パネルの実在検査
3. 内部リンク切れゼロ検査
4. 公式リンク死活検査（check_official_links.py。対象ドメインに city.fukuroi.shizuoka.jp／supportnavi.jp を追加）
5. inject_parts.py の冪等性（実行後diffゼロ）
6. **台帳整合検査**：公開ディレクトリに存在する全ページが `status: human-verified` 以上であること、`verified_date` がページ内表示と一致すること
7. sitemap.xml・search-index.json が台帳と一致すること（磐田のbuild-search-index.mjsを流用）

### 6.3 未検証ページを公開させない仕組み

生成スクリプトは `human-verified` 未満の項目を `_staging/`（.assetsignore対象・非配信）に出力し、`human-verified` 以上のみ `life/` に出力する。「うっかり未検証ページがデプロイされる」経路を構造的に断つ。検証が済んだらstatusを更新して再生成するだけで公開側へ移る。

---

## 7. 公開手順（段階公開）

一括公開はしない。検証ボトルネックと整合する3段階とする。

**Phase 1（骨格公開）**
トップ＋13カテゴリハブ＋利用規約＋404のみで公開。ハブには「順次公開中」の表示を入れ、未公開中項目はリンクなしのグレー表示とする。この時点でCloudflare設定確認（§3.3）、robots.txt、©表示、Search Console登録（sitemap送信）、Web Analytics稼働を済ませる。

**Phase 2（優先カテゴリ公開）**
CVと需要から、検証の優先順位を「①親のこと ②家・住まい ③人生の終わり ④困った・相談 ⑤これから暮らす」とし、human-verifiedになったカテゴリから順次公開する。①〜③は介護×不動産×相続の中核導線であり、袋井でCVを立ち上げる最短経路。

**Phase 3（全項目公開＋定常運用）**
残カテゴリを順次公開。全公開後に週次リンク監視（link-check.yml、磐田で待機中のワークフローを袋井にも複製し、有効化はまとめて判断）へ移行。フッターの遠州ネットワーク表記を磐田・袋井両リポジトリで最終化する。

各Phaseの完了条件は `inspect_all.py` の全項目パスとする。

---

## 8. 検収基準（Done定義）

1. `https://fukuroi.enshu-lifehack.com/` が200・HTTPS・カスタムドメインで配信されている
2. inspect_all.py 全項目パス（空style=0／タブ欠陥=0／内部リンク切れ=0／公式リンクエラー=0／冪等性OK／台帳整合OK）
3. 公開全ページに最終確認日・©表示・利用規約リンク・enshu-footerが揃っている
4. robots.txtがAI学習クローラー拒否＋fukuroi版Sitemap行になっている
5. 磐田側フッターに袋井が「運用中」として反映され、相互リンクが機能している
6. 検索（search-index.json）が袋井の公開項目のみを返す
7. topics_master.json上で published 件数＝公開HTML件数が一致する

---

## 9. 実施体制と分担

| 工程 | 担当 | 備考 |
|---|---|---|
| リポジトリ作成・磐田剥がし・Cloudflare接続 | Claude Code＋大石（ダッシュボード操作） | 半日 |
| 磐田列の自動抽出・台帳初期化 | Claude Code | 半日 |
| 袋井列のAI下調べ（155項目） | Claude Code／チャット | カテゴリ単位で分割実行 |
| **人力検証（クリティカルパス）** | **大石** | カテゴリ単位・優先順は§7 |
| ページ生成・検査・公開 | Claude Code | 検証済みカテゴリごと |
| 本番検証・進捗レビュー | このチャット（レビュー役） | 磐田で確立した分担を継続 |

Claude Codeへの指示文は本指示書を参照させた上で工程ごとに分割して出す（一括指示は差分検証が困難になるため。磐田第2弾の教訓を維持）。

---

## 10. リスクと予防

- **誤情報**：最大のリスク。対策は§5.2のstatus管理と§6.3の未検証非公開の構造化。磐田本文の置換流用禁止を徹底する
- **市サイトのURL変更**：磐田で301が3件/377本の実績。週次死活監視＋最終確認日で運用吸収する
- **磐田との共通資産の乖離**：2市の間はコピー同期とし、変更時は「両リポジトリのparts/を同時に直す」を規約化。3市目で共通化を再設計する
- **Cloudflare無料枠**：Rate Limitingルールはゾーン共用1本で全市をカバー。KVは使わない。Pages無料枠のビルド回数は現運用ペースで問題なし
- **検証疲れ**：155項目×以後7市町を同じ密度でやると破綻する。袋井で「県・国リンクは流用可」「CMS同系統はパス推測が効く」等の省力パターンを台帳のtierとnotesに記録し、3市目以降の検証単価を下げることを袋井の隠れた成果物とする

---

## 付録A：磐田版の現況（複製元の確定状態）

- 155中項目・13カテゴリ（困った・相談19／暮らし始めた16／働く・暮らす15／家族が増える13／健康・医療13／もしもの時12／人生の終わり11／家・住まい11／学ぶ・育つ10／親のこと10／遊ぶ・使う・出かける10／これから暮らす8／新しい場所へ7）
- 全157HTML：enshu-footer統一・site.css外部化・parts部品化・冪等性確認済み
- 公式リンク：ユニーク377本（磐田市公式2,377リンク箇所・県37・国系ほか）、エラー0・301が3件差し替え待ち
- スクレイピング対策：Bot Fight Mode／AI bot policies（Training=Block）／Rate Limiting／robots.txt 12種拒否／©表示＋利用規約

## 付録B：袋井市の公式情報源（初期調査済み）

- 公式サイト：https://www.city.fukuroi.shizuoka.jp/（CMSパスは /kurashi_tetsuzuki/… 系で磐田と同系統）
- 手続きナビ：https://fukuroi-city.supportnavi.jp/（ライフイベント別の手続き案内）
- 市役所：〒437-8666 袋井市新屋1-1-1／0538-43-2111／浅羽支所あり（届出・証明の多くは両所で受付）
- 消防・救急：袋井市森町広域行政組合（森町版展開時に共用できる調査資産）
- 市の特徴：高齢化率県内低位・年少人口割合は県内で高い水準（子育て系カテゴリの需要が相対的に高い可能性）。ただし2026-07-02にページ生成時の一次情報確認で総人口自体は緩やかな減少傾向（令和7年度当初87,635人→令和8年3月時点87,395人）と判明。「人口増加傾向」という当初の想定は誤りだったため訂正する

以上
