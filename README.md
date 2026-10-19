# ポータル試作：朝の情報収集と検索API

毎朝、決まった情報源の一覧ページを確認し、地域活動者向けの情報と、法人・団体づくりの情報を集める試作です（2026-10-20開始）。

- `sources.json`：確認する情報源。候補は `candidates_not_yet_checked`
- `items.jsonl`：1行1件の構造化データ。まとめ・APIすべての正本
- `daily/YYYY-MM-DD.md`：人が読むその日のまとめ。`python3 tools/render_daily.py [日付]` で items.jsonl から自動生成する（手で書かない）
- `api/server.py`・`api/openapi.json`：検索APIの試作（動的版）
- `tools/build_site.py`：items.jsonl から公開用の静的サイト（記事ページ、JSON-LD、静的API、llms.txt、robots.txt）を生成。`python3 tools/build_site.py 出力先 --base-url https://公開URL`

## 分類の考え方
大きな区分（section）は「地域活動者向け」と「法人・団体づくり」の2つです。地域活動者は退職者に限らず、企業で働く以外の居場所や役割を求める若い人、日本で地域コミュニティを作りたい外国人なども含みます。誰向けかは audience タグで表します。

## items.jsonl の項目
| 項目 | 意味 |
| --- | --- |
| id | `YYYY-MM-DD-NNN`（収集日＋連番） |
| section | 地域活動者向け / 法人・団体づくり |
| title / url | 元ページの題名とURL |
| abstract | 本文を読んで書いた100字以内の要約。日時・場所・対象・費用・申込状況を優先し、推測は書かない |
| status | 受付中 / 受付前 / 受付終了 / 申込不要 / お知らせ |
| event_dates / deadline | 開催日（複数可）と申込締切 |
| capacity | 定員（ページに書かれている場合のみ） |
| demand_signals | 人気の手がかりとしてページに出ている表示（先着順、定員に達しました、抽選、受付延長、追加募集など）。毎朝の確認で増えた表示は追記する。おすすめ指標の検討材料（指標自体は保留中） |
| source | sources.json の id |
| updated | 元サイトに出ている更新日 |
| region | 蕨市 / 川口市 / 埼玉県 / 全国 |
| category | イベント、講座・催し、ボランティア養成、高齢者スポーツ、地域団体、法人制度、税制、セミナー |
| audience | 退職者、高齢者、若者、外国人、子育て世代、地域団体、法人設立希望者、法人運営者（複数可） |
| languages | 情報が読める言語（ja、en など） |
| related | 関連する他の item の id |
| sponsored | 有料掲載なら true（AIにも人にも明示する） |
| verified_body / checked_at | 本文を確認したか、確認した日 |
| note | 補足（任意） |

同じURLが既に items.jsonl にあれば追加しません。

## APIの動かし方
```
cd api && python3 server.py 8000
```
| エンドポイント | 内容 |
| --- | --- |
| `GET /v1/items?section=&region=&category=&audience=&status=&since=&q=` | 検索（更新日の新しい順）。`fields=summary` で題名・要約・状態・日程・URLだけを返す |
| `GET /v1/items/{id}` | 1件の詳細。related を中身ごと展開 |
| `GET /v1/sources` | 情報源の一覧 |
| `GET /v1/stats/references` | 各情報が何回返されたか、うちAIからが何回か |
| `GET /openapi.json`・`GET /llms.txt` | AI向けの仕様と案内 |

返した情報と User-Agent は `logs/references.jsonl` に記録され、AIからの参照数（AI視聴率）の試作になっています。
