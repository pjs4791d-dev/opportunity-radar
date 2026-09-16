"""소스별 목록 파싱만 빠르게 점검 (상세 열람 X). 결과: 건수 / 첫 항목 / 오류.
  .venv/bin/python collector/check_sources.py [id접두어,...]
"""
import sys, pathlib, yaml, traceback
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fetch
from parsers import resolve
ROOT = pathlib.Path(__file__).resolve().parent.parent
S = yaml.safe_load((ROOT / "sources" / "sources.yaml").read_text(encoding="utf-8"))["sources"]
pre = sys.argv[1].split(",") if len(sys.argv) > 1 else None
skip = sys.argv[2].split(",") if len(sys.argv) > 2 else []
for s in S:
    if s["method"] not in ("html", "api") or s["url"] == "TODO":
        continue
    if pre and not any(s["id"].startswith(p) for p in pre):
        continue
    if any(s["id"].startswith(p) for p in skip):
        continue
    fn, opts = resolve(s)
    try:
        r = fn(s, {"get": fetch.get, "final_url": s["url"]}, **opts)
        first = (r[0]["title"][:45] + " | " + r[0]["url"][:60]) if r else ""
        print(f"{'ok ' if r else 'ZERO'} {s['id']:28s} {len(r):3d}  {first}", flush=True)
    except Exception as e:
        print(f"ERR  {s['id']:28s}      {type(e).__name__}: {str(e)[:100]}", flush=True)
