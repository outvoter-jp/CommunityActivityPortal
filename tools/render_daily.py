"""items.jsonl から朝のまとめ（daily/YYYY-MM-DD.md）を作る

使い方: python3 render_daily.py [YYYY-MM-DD]   （省略時は今日 JST）
その日に集めた件（id がその日付で始まる件）を新着として並べ、
既存の件のうち受付中・受付前で締切が近いものも「締切が近い」として載せる。
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))
STATUS_ORDER = {"受付中": 0, "受付前": 1, "申込不要": 2, "お知らせ": 3, "受付終了": 4}
SECTIONS = ("地域活動者向け", "法人・団体づくり")


def line(i):
    dates = "・".join(d[5:].replace("-", "/") for d in i.get("event_dates", []))
    meta = "、".join(x for x in (i.get("region"), i.get("status"), f"開催 {dates}" if dates else "") if x)
    tags = " ".join(f"#{a}" for a in i.get("audience", []))
    pr = "【PR】" if i.get("sponsored") else ""
    return f"- {pr}**[{i['title']}]({i['url']})**（{meta}）\n  {i.get('abstract', '')} {tags}"


def render(day):
    items = [json.loads(l) for l in (ROOT / "items.jsonl").open(encoding="utf-8") if l.strip()]
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["sources"]
    new = [i for i in items if i["id"].startswith(day)]
    soon_limit = (date.fromisoformat(day) + timedelta(days=14)).isoformat()
    soon = [i for i in items if i not in new and i.get("status") in ("受付中", "受付前")
            and day <= i.get("deadline", "9999") <= soon_limit]

    out = [f"# 地域活動・法人制度 朝の情報（{day}）", "",
           f"確認した情報源：{'、'.join(s['name'] for s in sources)}",
           f"新着 {len(new)} 件。元データは `items.jsonl`（このまとめは tools/render_daily.py で自動生成）", ""]
    for sec in SECTIONS:
        rows = sorted((i for i in new if i.get("section") == sec), key=lambda i: STATUS_ORDER.get(i.get("status"), 9))
        if rows:
            out += [f"## {sec}", ""] + [line(i) for i in rows] + [""]
    if soon:
        out += ["## 締切が近い（2週間以内）", ""]
        out += [line(i) + f"（締切 {i['deadline'][5:].replace('-', '/')}）" for i in sorted(soon, key=lambda i: i["deadline"])] + [""]
    if not new and not soon:
        out += ["新着はありませんでした。", ""]
    path = ROOT / "daily" / f"{day}.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


if __name__ == "__main__":
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.now(JST).date().isoformat()
    print(render(day))
