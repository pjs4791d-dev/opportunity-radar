"""제목·본문에서 마감일 / 행사일을 뽑는다 (명세서 5-2).

- 마감 계열 키워드: 신청기간, 접수기간, 모집기간, 마감, 접수, 신청, ~
- 행사 계열 키워드: 일시, 행사일, 교육기간, 진행일정, 개최
- 연도 없는 날짜는 기준일(posted) 연도를 붙이되, 기준일보다 4개월 이상 과거면 다음 해로 본다.
- 못 찾으면 None. 추측해서 채우지 않는다.
"""
import re, datetime

_D_FULL = r"(20\d{2})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})\s*일?\.?"
_D_SHORT = r"(?<!\d)(\d{1,2})\s*[./월]\s*(\d{1,2})\s*일?\.?(?!\d)"
DEADLINE_KW = r"(신청\s*기간|접수\s*기간|모집\s*기간|신청\s*마감|접수\s*마감|마감|접수|신청|모집|기한|까지|~|～|-)"
EVENT_KW = r"(일시|행사일|행사\s*일정|교육\s*기간|교육\s*일정|진행\s*일정|진행\s*기간|개최일|운영\s*기간|훈련\s*기간|시행일|일정)"


def _mk(y, m, d):
    try:
        return datetime.date(int(y), int(m), int(d))
    except ValueError:
        return None


def _infer_year(m, d, base):
    """연도 없는 M.D → base 연도 기준. base 보다 120일 넘게 과거면 다음 해."""
    if base is None:
        base = datetime.date.today()
    cand = _mk(base.year, m, d)
    if cand is None:
        return None
    if (base - cand).days > 120:
        cand = _mk(base.year + 1, m, d)
    return cand


def find_dates(text, base=None):
    """텍스트에 나오는 모든 날짜를 등장 순서대로 (date, 위치) 로 반환."""
    out = []
    taken = []
    for m in re.finditer(_D_FULL, text):
        dt = _mk(*m.groups())
        if dt:
            out.append((dt, m.start()))
            taken.append((m.start(), m.end()))
    for m in re.finditer(_D_SHORT, text):
        if any(a <= m.start() < b for a, b in taken):
            continue
        # 전화번호·금액 등 오탐 방지: 앞뒤가 숫자·콜론이면 제외
        before = text[max(0, m.start() - 1):m.start()]
        after = text[m.end():m.end() + 1]
        if before in "-:" or after in ":":
            continue
        mo, da = int(m.group(1)), int(m.group(2))
        if not (1 <= mo <= 12 and 1 <= da <= 31):
            continue
        dt = _infer_year(mo, da, base)
        if dt:
            out.append((dt, m.start()))
    out.sort(key=lambda x: x[1])
    return out


def _window_dates(text, kw_re, base, width=60):
    """키워드 뒤 width 글자 안의 날짜들을 (키워드별로) 모은다."""
    hits = []
    for m in re.finditer(kw_re, text):
        seg = text[m.end():m.end() + width]
        ds = [d for d, _ in find_dates(seg, base)]
        if ds:
            hits.append(ds)
    return hits


def extract(title, body="", posted=None):
    """→ (deadline, event_date) 각각 date 또는 None."""
    base = posted or datetime.date.today()
    text = " ".join(x for x in (title, body) if x)
    text = re.sub(r"\s+", " ", text)

    deadline = None
    event = None

    # 1) 제목의 (~9.17) / ~9/17 / 9.17까지 패턴이 가장 신뢰도 높음
    t = title or ""
    m = re.search(r"[~～]\s*" + _D_FULL, t) or re.search(r"[~～]\s*" + _D_SHORT, t)
    if m:
        g = m.groups()
        deadline = _mk(*g) if len(g) == 3 else _infer_year(g[0], g[1], base)
    if deadline is None:
        m = re.search(_D_FULL + r"\s*\(?[월화수목금토일]?\)?\s*까지", t) or re.search(_D_SHORT + r"\s*\(?[월화수목금토일]?\)?\s*까지", t)
        if m:
            g = m.groups()
            deadline = _mk(*g) if len(g) == 3 else _infer_year(g[0], g[1], base)

    # 2) 본문: 마감 키워드 창 → 기간이면 마지막 날짜
    if deadline is None:
        for ds in _window_dates(text, r"(신청\s*기간|접수\s*기간|모집\s*기간|신청\s*마감|접수\s*마감|마감\s*일?|접수\s*:|신청\s*:)", base, 70):
            deadline = ds[-1] if len(ds) >= 2 else ds[0]
            break

    # 3) 행사일: 키워드 창의 첫 날짜
    for ds in _window_dates(text, EVENT_KW, base, 50):
        event = ds[0]
        break

    return deadline, event


def to_iso(d):
    return d.isoformat() if d else None
