"""중복 제거 (명세서 5-3): 제목 정규화 후 유사도 0.85 이상 + 마감일 동일 → 같은 공고.
대표 URL 은 주최 기관 원문(대학·기관 게시판)을 우선, 나머지는 also_at 에 넣는다."""
import re, difflib

AGG_HOSTS = ("youth.seoul.go.kr", "campustown.seoul.go.kr", "youthcenter.go.kr", "k-startup.go.kr", "job.alio.go.kr")


def norm(t):
    t = re.sub(r"\[[^\]]*\]|\([^)]*\)|【[^】]*】|<[^>]*>|＜[^＞]*＞", " ", t or "")
    t = re.sub(r"[^0-9A-Za-z가-힣]+", "", t.lower())
    return t


def _is_agg(url):
    return any(h in url for h in AGG_HOSTS)


def dedupe(items, threshold=0.85):
    kept = []
    for it in items:
        n = norm(it["title"])
        dup = None
        for k in kept:
            if k["deadline"] != it["deadline"]:
                continue
            kn = norm(k["title"])
            if not n or not kn:
                continue
            if n == kn or difflib.SequenceMatcher(None, n, kn).ratio() >= threshold:
                dup = k
                break
        if dup is None:
            it.setdefault("also_at", [])
            kept.append(it)
            continue
        # 어느 쪽을 대표로 둘지: 집계 사이트가 아닌 쪽
        if _is_agg(dup["url"]) and not _is_agg(it["url"]):
            it["also_at"] = sorted(set(dup.get("also_at", []) + [dup["url"]]))
            it["first_seen"] = min(dup.get("first_seen") or it["first_seen"], it["first_seen"])
            kept[kept.index(dup)] = it
        else:
            dup["also_at"] = sorted(set(dup.get("also_at", []) + [it["url"]]))
    return kept
