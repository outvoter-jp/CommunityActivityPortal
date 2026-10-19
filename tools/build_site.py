"""items.jsonl から公開用の静的サイトを作る

使い方: python3 build_site.py [出力先] [--base-url https://example.org] [--preview]
  出力先の既定は ../site
  --preview を付けると、トップページを Claude の Artifact プレビュー用（doctype なし）で出す
生成物:
  index.html, items/<id>.html          人が読むページ（各記事に schema.org JSON-LD）
  api/v1/items.json, api/v1/items/<id>.json, api/v1/sources.json   静的API
  api/v1/sections/<slug>.json, api/v1/regions/<slug>.json        よく使う絞り込み
  openapi.json, llms.txt, robots.txt, sitemap.xml
"""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_NAME = "わたしらしく、地域とつながる。"
SECTIONS = {"地域活動者向け": "community", "法人・団体づくり": "organizing"}
REGIONS = {"蕨市": "warabi", "川口市": "kawaguchi", "埼玉県": "saitama", "全国": "national"}
STATUS_ORDER = {"受付中": 0, "受付前": 1, "申込不要": 2, "お知らせ": 3, "受付終了": 4}
STATUS_CLASS = {"受付中": "open", "受付前": "soon", "申込不要": "free", "お知らせ": "info", "受付終了": "closed"}

CSS = """
:root{--paper:#f6f8f4;--ink:#1d2a22;--muted:#56645b;--line:#d8e0d6;--fern:#2f6b3f;--fern-soft:#e3eee2;
--open:#1f6b45;--open-bg:#dcefe3;--soon:#7a5a00;--soon-bg:#f6ecc9;--closed:#5d6660;--closed-bg:#e7ebe7;--info:#2b4f7a;--info-bg:#e0e9f5;
--body:"BIZ UDPGothic","Hiragino Sans","Noto Sans JP",sans-serif;--display:"Zen Old Mincho","Hiragino Mincho ProN","Noto Serif JP",serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#141a16;--ink:#e6ece6;--muted:#a3b0a6;--line:#2c3830;--fern:#8fc79b;--fern-soft:#1f2c23;
--open:#9ad8b2;--open-bg:#1d3427;--soon:#e6c770;--soon-bg:#3a3117;--closed:#a9b2ab;--closed-bg:#262d28;--info:#a9c5ec;--info-bg:#1e2a3a;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#141a16;--ink:#e6ece6;--muted:#a3b0a6;--line:#2c3830;--fern:#8fc79b;--fern-soft:#1f2c23;
--open:#9ad8b2;--open-bg:#1d3427;--soon:#e6c770;--soon-bg:#3a3117;--closed:#a9b2ab;--closed-bg:#262d28;--info:#a9c5ec;--info-bg:#1e2a3a;color-scheme:dark}
body{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.75;margin:0}
.wrap{max-width:46rem;margin:0 auto;padding-block:1.5rem 3rem;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header.site{display:flex;flex-direction:column;gap:.25rem;border-bottom:2px solid var(--fern);padding-bottom:1rem;margin-bottom:1.25rem}
.site-name{font-family:var(--display);font-size:1.6rem;font-weight:600;line-height:1.3;text-wrap:balance;color:var(--ink);text-decoration:none}
.lead{color:var(--muted);font-size:.95rem;margin:0}
nav.sections{display:flex;flex-wrap:wrap;gap:.5rem;margin:.75rem 0 0}
nav.sections a,.chip-link{font-size:.9rem;padding:.25rem .75rem;border:1px solid var(--line);border-radius:999px;color:var(--ink);text-decoration:none;background:var(--paper)}
nav.sections a:hover,nav.sections a:focus-visible{border-color:var(--fern);outline:none}
h2{font-family:var(--display);font-size:1.25rem;font-weight:600;margin:2rem 0 .75rem;padding-left:.6rem;border-left:4px solid var(--fern)}
ul.items{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:.75rem}
.item{display:flex;flex-direction:column;gap:.35rem;padding:.9rem 1rem;border:1px solid var(--line);border-radius:6px;background:var(--paper);min-width:0}
.item.is-closed{opacity:.82}
.meta{display:flex;flex-wrap:wrap;gap:.4rem .75rem;align-items:center;font-size:.85rem;color:var(--muted);font-variant-numeric:tabular-nums}
.status{font-size:.8rem;font-weight:700;padding:.05rem .55rem;border-radius:4px;letter-spacing:.04em}
.status.open{color:var(--open);background:var(--open-bg)}.status.soon{color:var(--soon);background:var(--soon-bg)}
.status.closed{color:var(--closed);background:var(--closed-bg)}.status.info,.status.free{color:var(--info);background:var(--info-bg)}
.item h3{font-size:1.05rem;margin:0;line-height:1.5;text-wrap:balance}
.item h3 a{color:var(--ink);text-decoration:none}.item h3 a:hover,.item h3 a:focus-visible{color:var(--fern);text-decoration:underline}
.abstract{margin:0;overflow-wrap:anywhere}
.tags{display:flex;flex-wrap:wrap;gap:.35rem;font-size:.8rem}
.tags span{color:var(--fern);background:var(--fern-soft);padding:0 .5rem;border-radius:3px}
a{color:var(--fern)}
dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:.35rem 1rem;margin:1rem 0;font-size:.95rem}
dl.facts dt{color:var(--muted)}dl.facts dd{margin:0;min-width:0;overflow-wrap:anywhere}
.note{font-size:.85rem;color:var(--muted);border-top:1px solid var(--line);padding-top:1rem;margin-top:2rem}
code{font-size:.85em;background:var(--fern-soft);padding:0 .3rem;border-radius:3px;overflow-wrap:anywhere}
"""

HEAD_LINKS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
              '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&family=Zen+Old+Mincho:wght@600&display=swap">')

e = html.escape


def page(title, body, rel="", extra_head="", fragment=False):
    head = (f'<title>{e(title)}</title><meta name="claude:viewport-fit-sides" content="cover">'
            f'<meta name="description" content="蕨市・川口市の地域活動と、法人・団体づくりの最新情報。">'
            f'<link rel="alternate" type="text/plain" href="{rel}llms.txt" title="llms.txt">'
            f'<link rel="alternate" type="application/json" href="{rel}api/v1/items.json">'
            f'{HEAD_LINKS}<style>{CSS}</style>{extra_head}')
    if fragment:
        return head + body
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">{head}</head>'
            f'<body>{body}</body></html>')


def header(rel):
    links = "".join(f'<a href="{rel}index.html#{slug}">{e(name)}</a>' for name, slug in SECTIONS.items())
    return (f'<header class="site"><a class="site-name" href="{rel}index.html">{e(SITE_NAME)}</a>'
            f'<p class="lead">【試作版】蕨市・川口市の地域活動と、法人・団体づくりの情報を毎朝確認して載せています。</p>'
            f'<nav class="sections" aria-label="区分">{links}<a href="{rel}llms.txt">AI向けの案内</a></nav></header>')


def fmt_dates(i):
    return "・".join(f"{int(d[5:7])}/{int(d[8:])}" for d in i.get("event_dates", []))


def card(i, rel):
    st = i.get("status", "")
    meta = [f'<span class="status {STATUS_CLASS.get(st, "info")}">{e(st)}</span>', f'<span>{e(i.get("region", ""))}</span>']
    if fmt_dates(i):
        meta.append(f'<span>開催 {fmt_dates(i)}</span>')
    if i.get("deadline") and st in ("受付中", "受付前"):
        meta.append(f'<span>締切 {int(i["deadline"][5:7])}/{int(i["deadline"][8:])}</span>')
    if i.get("sponsored"):
        meta.append('<span class="status soon">PR</span>')
    tags = "".join(f"<span>{e(a)}</span>" for a in i.get("audience", []))
    closed = " is-closed" if st == "受付終了" else ""
    return (f'<li class="item{closed}"><div class="meta">{"".join(meta)}</div>'
            f'<h3><a href="{rel}items/{i["id"]}.html">{e(i["title"])}</a></h3>'
            f'<p class="abstract">{e(i.get("abstract", ""))}</p><div class="tags">{tags}</div></li>')


def json_ld(i, base):
    url = f"{base}/items/{i['id']}.html" if base else f"items/{i['id']}.html"
    common = {"@context": "https://schema.org", "name": i["title"], "description": i.get("abstract", ""),
              "url": url, "sameAs": i["url"], "inLanguage": "ja", "dateModified": i.get("checked_at")}
    if i.get("event_dates"):
        return {**common, "@type": "Event", "startDate": i["event_dates"][0], "endDate": i["event_dates"][-1],
                "location": {"@type": "Place", "name": i.get("region", ""),
                             "address": {"@type": "PostalAddress", "addressRegion": "埼玉県", "addressLocality": i.get("region", "")}},
                "eventStatus": "https://schema.org/EventScheduled", "audience": [{"@type": "Audience", "audienceType": a} for a in i.get("audience", [])]}
    return {**common, "@type": "NewsArticle", "headline": i["title"], "datePublished": i.get("updated")}


def detail(i, by_id, base):
    rel = "../"
    rows = [("区分", i.get("section")), ("状況", i.get("status")), ("地域", i.get("region")), ("分類", i.get("category")),
            ("開催日", fmt_dates(i)), ("申込締切", i.get("deadline")), ("元ページの更新日", i.get("updated")),
            ("本文の確認日", i.get("checked_at"))]
    facts = "".join(f"<dt>{k}</dt><dd>{e(str(v))}</dd>" for k, v in rows if v)
    related = [by_id[r] for r in i.get("related", []) if r in by_id]
    rel_html = (f'<h2>関連する情報</h2><ul class="items">{"".join(card(r, rel) for r in related)}</ul>' if related else "")
    body = (f'<div class="wrap">{header(rel)}<article><h1 class="site-name" style="font-size:1.4rem">{e(i["title"])}</h1>'
            f'<p class="abstract">{e(i.get("abstract", ""))}</p><dl class="facts">{facts}</dl>'
            f'<p><a href="{e(i["url"])}" target="_blank" rel="noopener">元のページを開く（正式な情報はこちら）</a></p>'
            f'<p class="note">この要約は元ページを読んで作成したものです。日時や申込方法は必ず元のページでご確認ください。'
            f'機械で読む場合は <a href="{rel}api/v1/items/{i["id"]}.json"><code>api/v1/items/{i["id"]}.json</code></a></p>'
            f'</article>{rel_html}</div>')
    ld = f'<script type="application/ld+json">{json.dumps(json_ld(i, base), ensure_ascii=False)}</script>'
    return page(f"{i['title']}｜{SITE_NAME}", body, rel, ld)


def index(items, fragment):
    parts = [f'<div class="wrap">{header("")}']
    for name, slug in SECTIONS.items():
        rows = sorted((i for i in items if i.get("section") == name),
                      key=lambda i: (STATUS_ORDER.get(i.get("status"), 9), (i.get("event_dates") or ["9999"])[0]))
        parts.append(f'<h2 id="{slug}">{e(name)}<span class="lead" style="font-family:var(--body);font-size:.85rem"> {len(rows)}件</span></h2>')
        parts.append(f'<ul class="items">{"".join(card(i, "") for i in rows)}</ul>')
    parts.append('<p class="note">情報は各自治体・団体の公開ページを毎朝確認し、要約を付けて掲載しています。'
                 '受付が終わった催しも、次回の参考として残しています。AIやプログラムからは '
                 '<a href="api/v1/items.json"><code>api/v1/items.json</code></a> と '
                 '<a href="openapi.json"><code>openapi.json</code></a> で同じ情報を取得できます。</p></div>')
    return page(SITE_NAME, "".join(parts), "", "", fragment)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(out, base, preview):
    items = [json.loads(l) for l in (ROOT / "items.jsonl").open(encoding="utf-8") if l.strip()]
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    by_id = {i["id"]: i for i in items}
    if out.exists():
        shutil.rmtree(out)
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=2)

    write(out / "index.html", index(items, preview))
    for i in items:
        write(out / "items" / f"{i['id']}.html", detail(i, by_id, base))
        expanded = dict(i, related=[by_id[r] for r in i.get("related", []) if r in by_id])
        write(out / "api/v1/items" / f"{i['id']}.json", dump(expanded))
    write(out / "api/v1/items.json", dump({"count": len(items), "items": items}))
    write(out / "api/v1/sources.json", dump(sources))
    for name, slug in SECTIONS.items():
        rows = [i for i in items if i.get("section") == name]
        write(out / f"api/v1/sections/{slug}.json", dump({"section": name, "count": len(rows), "items": rows}))
    for name, slug in REGIONS.items():
        rows = [i for i in items if i.get("region") == name]
        if rows:
            write(out / f"api/v1/regions/{slug}.json", dump({"region": name, "count": len(rows), "items": rows}))

    llms = [f"# {SITE_NAME}", "", "> 試作版。蕨市・川口市の地域活動と、法人・団体づくりの情報。各件に本文を読んで書いた100字以内の要約、申込状況、開催日、出典URL、確認日を付けています。正式な情報は各件の出典URLを参照してください。", "",
            "## 機械で読む", "- [全件JSON](api/v1/items.json)", "- [地域活動者向け](api/v1/sections/community.json)",
            "- [法人・団体づくり](api/v1/sections/organizing.json)", "- [OpenAPI仕様](openapi.json)", "- [情報源](api/v1/sources.json)", "",
            "## 掲載中の情報"]
    llms += [f"- [{i['title']}](items/{i['id']}.html): {i.get('abstract', '')}（{i.get('status', '')}）" for i in items]
    write(out / "llms.txt", "\n".join(llms) + "\n")

    spec = json.loads((ROOT / "api/openapi.json").read_text(encoding="utf-8"))
    spec["servers"] = [{"url": base or "/"}]
    spec["info"]["description"] += " 静的サイト版では /api/v1/items.json・/api/v1/sections/{slug}.json・/api/v1/regions/{slug}.json・/api/v1/items/{id}.json を提供（検索パラメータは動的API版のみ）。"
    write(out / "openapi.json", dump(spec))
    write(out / "robots.txt", "User-agent: *\nAllow: /\n" + (f"Sitemap: {base}/sitemap.xml\n" if base else ""))
    if base:
        urls = [f"{base}/"] + [f"{base}/items/{i['id']}.html" for i in items]
        write(out / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n")
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    preview = "--preview" in args
    base = ""
    if "--base-url" in args:
        base = args[args.index("--base-url") + 1].rstrip("/")
    rest = [a for a in args if not a.startswith("--") and a != base]
    out = Path(rest[0]) if rest else ROOT / "site"
    print(build(out.resolve(), base, preview))
