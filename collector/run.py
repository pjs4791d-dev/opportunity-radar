"""전체 수집 실행 진입점.

  .venv/bin/python collector/run.py                 # 전체 소스
  .venv/bin/python collector/run.py --only dgu-,kofia,work24,seoul-youth   # id 접두어로 일부만
  .venv/bin/python collector/run.py --no-detail     # 상세 페이지 안 열고 목록만 (빠른 점검)
  .venv/bin/python collector/run.py --no-notify

흐름: sources.yaml → 소스별 파서 → (신규 항목만) 상세 페이지에서 날짜·자격 근거 추출
     → 자격 판정 → 중복 제거 → seed·기존 항목과 병합 → programs.json / seen.json / errors.json / sources.json
     → 텔레그램 알림
"""
import sys, os, json, re, hashlib, datetime, argparse, pathlib, traceback, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import yaml
import fetch as H
import dates, eligibility, dedupe, classify, build_sources, notify
from parsers import resolve
from parsers.common import clean
from parsers.special import seoul_youth_detail

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
TODAY = datetime.date.today()
KEEP_DAYS_AFTER_DEADLINE = 0      # 마감일이 지나면 다음 수집부터 제거 (당일까지는 표시)
KEEP_DAYS_NO_DATE_POSTED = 30     # 날짜를 못 뽑은 글: 게시일 기준 보관 일수
KEEP_DAYS_NO_DATE_SEEN = 21       # 날짜·게시일 모두 없는 글: 처음 본 날 기준 보관 일수
MAX_DETAIL_PER_SOURCE = 10
JUNK_TITLE = re.compile(r"^(로그인|새창|새 창|갤러리|더보기|사이트맵|개인정보|이메일|Home|홈|목록|이전|다음|첨부|공지사항|검색|바로가기|자세히)|(페이지 이동|UOS 갤러리|스팸|피싱)$|^[^가-힣A-Za-z]*$")
# 기회가 아니라 '결과' 성격의 글: 합격자 발표, 선정 결과, 조치결과 등
RESULT_TITLE = re.compile(r"합격자|최종\s*합격|선발\s*결과|선정\s*결과|심사\s*결과|평가\s*결과|결과\s*(발표|안내|공고|공개)|조치결과|감사결과|당첨자|수상자\s*발표|면접\s*(시간|일정)\s*안내|사칭|주의\s*안내|이용자\s*만족도|서비스\s*중단|점검\s*안내|휴관|개인정보\s*처리방침|용역|입찰|제안서|교원\s*채용|전임교원|교직원\s*채용|조교\s*채용|축하\s*모임|시험\s*결과|일반대학원.*모집|대학원.*신입생\s*모집")        # 소스당 상세 페이지 열람 상한(신규 항목만)


def load_json(name, default):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def make_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def body_text(html):
    """상세 HTML → 본문 텍스트(스크립트·내비 제거)."""
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    for t in s(["script", "style", "nav", "header", "footer", "noscript"]):
        t.decompose()
    main = None
    for sel in (".board_view", ".view_con", ".bbs_view", ".board-view", ".artclView", ".b-content-box", ".view_content", ".detail_con", ".content_view",
                "article", ".view", ".detail", "#contents", ".contents", "#content", ".content", "main"):
        main = s.select_one(sel)
        if main and len(main.get_text(" ")) > 200:
            break
    main = main or s.body or s
    return clean(main.get_text(" "))[:6000]


def fetch_detail(url):
    if "#" in url:
        url = url.split("#")[0]
    try:
        html = H.get(url)
    except Exception as e:
        return "", str(e)[:100]
    return body_text(html), None


def collect_source(src, ctx_get, want_detail, seen, errors, stats):
    fn, opts = resolve(src)
    final = {"url": src["url"]}

    def _get(url, **kw):
        final["url"] = url
        return ctx_get(url, **kw)

    ctx = {"get": _get, "final_url": src["url"]}
    items = fn(src, ctx, **opts)
    ctx["final_url"] = final["url"]
    if not items:
        raise RuntimeError("파싱 결과 0건 (사이트 구조 변경?)")
    out = []
    detail_budget = MAX_DETAIL_PER_SOURCE
    for it in items:
        pid = make_id(it["url"])
        prev = seen.get(pid)
        is_new = prev is None
        body = ""
        if want_detail and is_new and detail_budget > 0 and src["method"] == "html":
            body, err = fetch_detail(it["url"])
            detail_budget -= 1
            stats["detail"] += 1
        elif prev and prev.get("body_hint"):
            body = prev["body_hint"]
        posted = it.get("posted")
        deadline, event = dates.extract(it["title"], body or it.get("text", ""), posted)
        extra = {}
        if src["id"] in ("seoul-youth-sprt", "seoul-orang") and body:
            sd = seoul_youth_detail(body)
            if sd.get("apply"):
                d2, _ = dates.extract("", "신청기간 " + sd["apply"], posted)
                deadline = d2 or deadline
            if sd.get("event"):
                _, e2 = dates.extract("", "진행일정 " + sd["event"], posted)
                event = e2 or event
            if sd.get("org"):
                it["org"] = sd["org"][:30]
            if sd.get("target"):
                extra["target"] = sd["target"][:60]
        scope = src.get("default_scope", "other_univ")
        # 규칙 판정은 매번 다시(규칙이 바뀌어도 반영), Claude API 는 신규 항목에만
        client, model = stats["claude"] if is_new else (None, None)
        ej = eligibility.judge(scope, it["title"], body or it.get("text", ""), client, model)
        if ej["eligibility"] == "check" and prev and prev.get("eligibility") in ("yes", "no") and prev.get("judged_by") == "claude":
            ej = {"eligibility": prev["eligibility"], "eligibility_reason": prev["eligibility_reason"], "dongguk_only": prev.get("dongguk_only", False)}
        if ej["eligibility"] == "check" and "target" in extra:
            ej["eligibility_reason"] = extra["target"]
        if JUNK_TITLE.search(it["title"]) or RESULT_TITLE.search(it["title"]):
            continue
        if src["id"].startswith("work24"):
            cat = "현장·기술직"
            m = re.search(r"(20\d{2}-\d{2}-\d{2})\s*~\s*(20\d{2}-\d{2}-\d{2})", it.get("period", ""))
            if m:
                event = datetime.date.fromisoformat(m.group(1))
                deadline = None   # 고용24 는 '모집중' 표시만 있고 접수 마감일은 상세에서 확인
        else:
            cat = it.get("category_hint") and ("교육·부트캠프" if "교육" in it["category_hint"] else None) or classify.category(it["title"], body[:300] or it.get("text", ""))
        if scope == "other_univ" and cat == "학사·행정" and ej["eligibility"] != "no":
            ej = {"eligibility": "no", "eligibility_reason": "학사·행정 공지 (해당 대학 재학생 대상)", "dongguk_only": False}
        p = {
            "id": pid,
            "title": it["title"],
            "org": it.get("org") or src["name"],
            "url": it["url"],
            "section": src["section"],
            "category": cat,
            "subcategory": classify.subcategory(cat, it["title"], it.get("text", "")),
            "eligibility": ej["eligibility"],
            "eligibility_reason": ej["eligibility_reason"],
            "dongguk_only": ej["dongguk_only"],
            "requires_card": bool(it.get("requires_card") or src.get("requires_card")),
            "posted": posted.isoformat() if posted else None,
            "deadline": deadline.isoformat() if deadline else None,
            "event_date": event.isoformat() if event else None,
            "source_id": src["id"],
            "university": src.get("university"),
            "group": src.get("group"),
            "campus": src.get("campus"),
            "first_seen": prev["first_seen"] if prev else TODAY.isoformat(),
            "recurring": None,
            "priority": 0,
            "keywords": [k for k in (src.get("university"), src.get("group"), cat, it.get("keyword")) if k],
            "format": it.get("period") or None,
            "cost": it.get("cost") or None,
            "location": it.get("location") or None,
            "state": it.get("state") or None,
            "benefit": (it.get("text") or "")[:160] or None,
            "also_at": [],
        }
        p["priority"] = classify.priority(p, TODAY)
        # 이미 지난 공고 / 오래된 글은 화면에 넣지 않는다 (seen 에는 기록)
        stale = not still_valid(p)
        if not stale:
            out.append(p)
        seen[pid] = {"url": it["url"], "title": it["title"], "first_seen": p["first_seen"], "last_seen": TODAY.isoformat(),
                     "eligibility": p["eligibility"], "eligibility_reason": p["eligibility_reason"], "dongguk_only": p["dongguk_only"],
                     "body_hint": (body or (prev or {}).get("body_hint") or "")[:800], "source_id": src["id"],
                     "judged_by": "claude" if (is_new and client and ej["eligibility"] != "check" and scope == "other_univ" and "AI" in ej.get("eligibility_reason", "")) else (prev or {}).get("judged_by")}
        if is_new and not stale:
            stats["new"].append(p)
    return out


class _SeenView(dict):
    """읽기는 공유 seen, 쓰기는 로컬에 모아 두는 얇은 래퍼 (스레드 안전한 병합용)."""
    def __init__(self, shared, local):
        self._s, self._l = shared, local
    def get(self, k, default=None):
        return self._l.get(k, self._s.get(k, default))
    def __setitem__(self, k, v):
        self._l[k] = v


def still_valid(p):
    """화면에 남길지: 마감 전(당일 포함) / 행사 전 / 날짜를 모르면 게시일·최초발견일 기준 일정 기간."""
    dl = p.get("deadline")
    if dl:
        try:
            return (TODAY - datetime.date.fromisoformat(dl[:10])).days <= KEEP_DAYS_AFTER_DEADLINE
        except ValueError:
            return True
    ev = p.get("event_date")
    if ev:
        try:
            if datetime.date.fromisoformat(ev[:10]) < TODAY:
                return False   # 마감일은 몰라도 행사일이 지났으면 끝난 것
        except ValueError:
            pass
        else:
            return True
    # 제목의 연도가 작년 이하이고 미래 날짜가 없으면 지난 공고
    m = re.search(r"(20\d{2})\s*(년|학년도|-\d)", p.get("title", ""))
    if m and int(m.group(1)) < TODAY.year:
        return False
    posted = p.get("posted")
    if posted:
        return (TODAY - datetime.date.fromisoformat(posted[:10])).days <= KEEP_DAYS_NO_DATE_POSTED
    fs = p.get("first_seen") or TODAY.isoformat()
    return (TODAY - datetime.date.fromisoformat(fs)).days <= KEEP_DAYS_NO_DATE_SEEN


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="쉼표로 구분한 source id 접두어")
    ap.add_argument("--no-detail", action="store_true")
    ap.add_argument("--no-notify", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="처리할 소스 수 상한(테스트용)")
    ap.add_argument("--workers", type=int, default=6, help="동시에 처리할 소스 수(도메인별로는 항상 직렬·2초 간격)")
    args = ap.parse_args()

    sources = yaml.safe_load((ROOT / "sources" / "sources.yaml").read_text(encoding="utf-8"))["sources"]
    targets = [s for s in sources if s["method"] in ("html", "api") and s["url"] != "TODO"]
    if args.only:
        pre = [x.strip() for x in args.only.split(",") if x.strip()]
        targets = [s for s in targets if any(s["id"].startswith(p) for p in pre)]
    if args.limit:
        targets = targets[:args.limit]

    seen = load_json("seen.json", {})
    if isinstance(seen, list):
        seen = {}
    old_programs = {p["id"]: p for p in load_json("programs.json", {"programs": []})["programs"]}
    old_errors = {e["source_id"]: e for e in load_json("errors.json", [])}
    status = load_json("source_status.json", {})
    stats = {"new": [], "detail": 0, "claude": eligibility.make_client()}
    errors = []
    collected = {}
    ok_sources = set()

    print(f"[{TODAY}] {len(targets)} sources, workers={args.workers}", file=sys.stderr)
    lock = threading.Lock()
    done = [0]

    def work(src):
        local_seen = {}
        local_stats = {"new": [], "detail": 0, "claude": stats["claude"]}
        # seen 은 읽기 공유, 쓰기는 로컬 dict 로 받아 메인에서 합친다
        view = _SeenView(seen, local_seen)
        items = collect_source(src, H.get, not args.no_detail, view, errors, local_stats)
        return items, local_seen, local_stats

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(work, src): src for src in targets}
        for fut in as_completed(futs):
            src = futs[fut]
            with lock:
                done[0] += 1
                i = done[0]
            try:
                items, local_seen, local_stats = fut.result()
                with lock:
                    seen.update(local_seen)
                    stats["new"].extend(local_stats["new"])
                    stats["detail"] += local_stats["detail"]
                    for p in items:
                        collected[p["id"]] = p
                    ok_sources.add(src["id"])
                    status[src["id"]] = {"last_success": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "last_error": None,
                                         "fail_count": 0, "last_count": len(items)}
                print(f"  ok  {i:3d}/{len(targets)} {src['id']:28s} {len(items):3d}건", file=sys.stderr)
            except Exception as e:
                msg = f"{type(e).__name__}: {str(e)[:160]}"
                with lock:
                    st = status.get(src["id"], {})
                    st.update({"last_error": msg, "fail_count": int(st.get("fail_count", 0)) + 1})
                    st.setdefault("last_success", None)
                    status[src["id"]] = st
                    errors.append({"source_id": src["id"], "name": src["name"], "url": src["url"], "error": msg,
                                   "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "fail_count": st["fail_count"]})
                print(f"  ERR {i:3d}/{len(targets)} {src['id']:28s} {msg}", file=sys.stderr)

    # 병합: 이번에 수집한 것 + (이번에 안 돈 소스의) 기존 항목 + 수동 seed
    merged = dict(collected)
    for pid, p in old_programs.items():
        if pid in merged:
            continue
        if JUNK_TITLE.search(p.get("title", "")) or RESULT_TITLE.search(p.get("title", "")):
            continue
        if p.get("source_id") in ok_sources:
            # 그 소스를 이번에 돌았는데 목록에서 사라짐 → 마감 전이면 잠시 유지
            if still_valid(p):
                merged[pid] = p
            continue
        if still_valid(p):
            merged[pid] = p
    programs = [p for p in merged.values() if p["eligibility"] != "no" or p.get("section") == "campus" and p.get("university") == "동국대"]
    programs = [p for p in programs if p["eligibility"] != "no"]
    programs = dedupe.dedupe(sorted(programs, key=lambda p: (p["source_id"] == "manual-seed", p["url"])))
    for p in programs:
        p["priority"] = classify.priority(p, TODAY)
    programs.sort(key=lambda p: -p["priority"])

    # 실패 목록: 이번에 돌린 소스는 이번 결과로 갱신, 나머지는 이전 값 유지
    err_map = {e["source_id"]: e for e in old_errors.values() if e["source_id"] not in {s["id"] for s in targets}}
    for e in errors:
        err_map[e["source_id"]] = e
    errors_out = sorted(err_map.values(), key=lambda e: -e.get("fail_count", 0))

    save_json("programs.json", {"generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                "count": len(programs), "user": CFG.get("user", {}), "programs": programs})
    save_json("seen.json", seen)
    save_json("errors.json", errors_out)
    save_json("source_status.json", status)
    build_sources.build(status)
    build_sources.build_recurring()

    new_yes = [p for p in stats["new"] if p["eligibility"] == "yes"]
    print(f"\n수집 {len(collected)}건 / 화면 {len(programs)}건 / 신규 {len(stats['new'])}건(참여가능 {len(new_yes)}) / 상세열람 {stats['detail']}회 / 실패 소스 {len(errors)}", file=sys.stderr)
    if not args.no_notify:
        notify.send_digest(programs, stats["new"], errors_out, TODAY)


if __name__ == "__main__":
    main()
