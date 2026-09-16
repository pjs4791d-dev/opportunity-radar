"""sources/sources.yaml → data/sources.json (화면의 '트래킹 소스' 탭용).

실행:  .venv/bin/python collector/build_sources.py
수집기(run.py)도 마지막에 이 함수를 호출해 last_success / last_error 를 채운다.
"""
import json, sys, datetime, pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "sources" / "sources.yaml"
OUT = ROOT / "data" / "sources.json"

# 화면 탭 분류
def screen_type(s):
    if s["section"] == "finance":
        return "금융·증권"
    if s["section"] == "trades":
        return "직업훈련"
    if s.get("university"):
        return "대학"
    if s.get("group") in ("민간 생태계", "서울 창업", "대외활동 모음"):
        return "창업·테크"
    return "서울시·공공"

def build(status=None):
    """status: {source_id: {"last_success": iso|None, "last_error": str|None}} (run.py 가 넘김)"""
    status = status or {}
    doc = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    out = []
    for s in doc["sources"]:
        st = status.get(s["id"], {})
        out.append({
            "id": s["id"],
            "name": s["name"],
            "section": s["section"],
            "type": screen_type(s),
            "group": s.get("group") or s.get("university") or "",
            "university": s.get("university"),
            "campus": s.get("campus"),
            "method": s["method"],
            "url": s["url"],
            "default_scope": s.get("default_scope"),
            "focus": s.get("note") or "",
            "todo": s["url"] == "TODO",
            "last_success": st.get("last_success"),
            "last_error": st.get("last_error"),
        })
    OUT.write_text(json.dumps({
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": out,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

def build_recurring():
    """data/recurring.yaml → data/recurring.json (금융 캘린더용)"""
    src = ROOT / "data" / "recurring.yaml"
    items = []
    if src.exists():
        items = (yaml.safe_load(src.read_text(encoding="utf-8")) or {}).get("items") or []
    (ROOT / "data" / "recurring.json").write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


if __name__ == "__main__":
    build_recurring()
    n = len(build())
    print(f"wrote {OUT} ({n} sources)")
