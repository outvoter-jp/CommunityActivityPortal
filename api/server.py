"""地域活動ポータル 試作API（標準ライブラリのみ）

起動: python3 server.py [port]   （既定 8000）
データ: ../items.jsonl と ../sources.json を毎リクエスト読み直す
参照ログ: ../logs/references.jsonl に、どの item を誰（User-Agent）に返したかを1行ずつ記録する
"""
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "items.jsonl"
SOURCES = ROOT / "sources.json"
LOG = ROOT / "logs" / "references.jsonl"

AI_AGENTS = ("ClaudeBot", "Claude-User", "Claude-SearchBot", "GPTBot", "ChatGPT-User", "OAI-SearchBot",
             "PerplexityBot", "Google-Extended", "anthropic", "openai", "mcp")


SUMMARY_FIELDS = ("id", "title", "abstract", "status", "event_dates", "url", "sponsored")


def load_items():
    with ITEMS.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def is_ai(user_agent):
    ua = (user_agent or "").lower()
    return any(a.lower() in ua for a in AI_AGENTS)


def log_references(ids, path, user_agent):
    LOG.parent.mkdir(exist_ok=True)
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "path": path,
             "user_agent": user_agent, "ai": is_ai(user_agent), "item_ids": ids}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def filter_items(items, q):
    def one(name):
        return q.get(name, [None])[0]

    out = items
    for field in ("section", "region", "category", "source", "status"):
        if one(field):
            out = [i for i in out if i.get(field) == one(field)]
    if one("audience"):
        out = [i for i in out if one("audience") in i.get("audience", [])]
    if one("since"):
        out = [i for i in out if i.get("updated", "") >= one("since")]
    if one("q"):
        out = [i for i in out if any(one("q") in i.get(k, "") for k in ("title", "abstract", "note"))]
    return sorted(out, key=lambda i: i.get("updated", ""), reverse=True)


def reference_stats():
    counts = {}
    if LOG.exists():
        with LOG.open(encoding="utf-8") as f:
            for line in f:
                e = json.loads(line)
                for i in e["item_ids"]:
                    c = counts.setdefault(i, {"total": 0, "ai": 0})
                    c["total"] += 1
                    c["ai"] += e["ai"]
    return [{"id": k, **v} for k, v in sorted(counts.items(), key=lambda kv: -kv[1]["ai"])]


def llms_txt(items):
    lines = ["# 地域活動ポータル（試作）", "",
             "> 蕨市・川口市の地域活動と、法人・団体づくりの最新情報。各件に出典URL・更新日・地域・対象者を付けています。", "",
             "## API", "- [OpenAPI仕様](/openapi.json)", "- [全件JSON](/v1/items)", "- [情報源](/v1/sources)", "",
             "## 最新の情報"]
    lines += [f"- [{i['title']}](/v1/items/{i['id']}): {i.get('abstract', '')}（{i.get('status', '')}）"
              for i in filter_items(items, {})[:30]]
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else (
            body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False, indent=2).encode())
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        ua = self.headers.get("User-Agent", "")
        items = load_items()
        by_id = {i["id"]: i for i in items}

        if url.path == "/v1/items":
            found = filter_items(items, q)
            log_references([i["id"] for i in found], url.path, ua)
            if q.get("fields", [""])[0] == "summary":
                found = [{k: i[k] for k in SUMMARY_FIELDS if k in i} for i in found]
            return self.send(200, {"count": len(found), "items": found})
        if url.path.startswith("/v1/items/"):
            item = by_id.get(url.path.rsplit("/", 1)[-1])
            if not item:
                return self.send(404, {"error": "not_found"})
            expanded = dict(item, related=[by_id[r] for r in item.get("related", []) if r in by_id])
            log_references([item["id"]], url.path, ua)
            return self.send(200, expanded)
        if url.path == "/v1/sources":
            return self.send(200, json.loads(SOURCES.read_text(encoding="utf-8")))
        if url.path == "/v1/stats/references":
            return self.send(200, {"items": reference_stats()})
        if url.path == "/openapi.json":
            return self.send(200, (Path(__file__).parent / "openapi.json").read_bytes())
        if url.path in ("/llms.txt", "/"):
            return self.send(200, llms_txt(items), "text/plain; charset=utf-8")
        return self.send(404, {"error": "not_found"})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"http://localhost:{port}/llms.txt")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
