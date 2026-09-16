"""링크 패턴 기반 범용 파서 (대부분의 대학 게시판이 여기에 해당)."""
import re
from urllib.parse import urljoin
from .common import soup, clean, first_date, container, item

# 게시판 상세 링크에서 흔히 보이는 패턴들 (순서 무관)
DEFAULT_PATTERNS = [
    r"artclView\.do", r"mode=view", r"articleNo=", r"wr_id=", r"/bbs/content/",
    r"/notice/\d+", r"view\.do\?", r"BoardView\.do", r"PostingDetail", r"recruitview\.do",
    r"/university_news/\d+", r"/sct_news/\d+", r"Read\.jsp", r"mod=document", r"read\.do\?",
    r"/detail/\d+", r"/programs/info/\d+", r"/news/notice/\d+", r"/dvic\d_\d+/\d+",
    r"/dvic2_2/\d+", r"/ko/o/\d+", r"noticeDetail\.do", r"/user/kmuNews/notice/\d+/\d+",
    r"portalBoardView", r"/board/notice/view", r"courseDetail\.do", r"/community/notice/\d+",
    r"/community/external/\d+", r"nttId=", r"idx=\d+", r"seq=\d+", r"uid=\d+",
]
SKIP_TEXT = re.compile(r"^(더보기|more|목록|이전|다음|처음|마지막|\d+|첨부파일|new|공지|top|home)$", re.I)


def link_regex(source, ctx, patterns=None, exclude=None, min_title=4, max_items=40, title_sel=None, date_sel=None):
    html = ctx["get"](source["url"])
    s = soup(html)
    pats = [re.compile(p) for p in (patterns or DEFAULT_PATTERNS)]
    excl = re.compile(exclude) if exclude else None
    seen, out = set(), []
    for a in s.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("javascript", "#", "mailto")):
            continue
        if not any(p.search(href) for p in pats):
            continue
        if excl and excl.search(href):
            continue
        url = urljoin(ctx["final_url"], href).replace("&amp;", "&")
        if url in seen:
            continue
        title = clean(a.get("title") or a.get_text(" "))
        if title_sel:
            t = a.select_one(title_sel)
            if t:
                title = clean(t.get_text(" "))
        title = re.sub(r"\s*(첨부파일 있음|새 창 열림|새창)\s*$", "", title)
        row = container(a)
        row_text = clean(row.get_text(" ")) if row else ""
        if len(title) < min_title and row is not None:
            tn = row.select_one(".tit, .title, td.title, .subject, td.left, .b-title-box, .text02, strong")
            title = clean(tn.get_text(" ")) if tn else ""
            if len(title) < min_title:
                cells = [clean(td.get_text(" ")) for td in row.find_all("td")]
                cells = [c for c in cells if len(c) >= 8 and not re.fullmatch(r"[\d.\-: ]+", c)]
                title = cells[0][:100] if cells else ""
        if len(title) < min_title or SKIP_TEXT.match(title):
            continue
        posted = first_date(row.select_one(date_sel).get_text()) if (date_sel and row and row.select_one(date_sel)) else first_date(row_text)
        seen.add(url)
        out.append(item(source, title, url, posted, row_text))
        if len(out) >= max_items:
            break
    return out


def onclick_regex(source, ctx, onclick, detail, max_items=40, title_from="anchor"):
    """onclick="fn('a','b')" 형태. onclick: 그룹이 있는 정규식, detail: 그룹으로 포맷할 URL 템플릿."""
    html = ctx["get"](source["url"])
    s = soup(html)
    rx = re.compile(onclick)
    seen, out = set(), []
    for el in s.find_all(attrs={"onclick": True}) + s.find_all("a", href=re.compile(r"^javascript:")):
        m = rx.search(el.get("onclick") or el.get("href") or "")
        if not m:
            continue
        url = detail.format(*m.groups())
        if url in seen:
            continue
        tnode = el.select_one(".tit, .subject, .title, td.left, td.title, .b-title-box, p.tit, strong.ti, .postTitle") if el.name != "a" else None
        title = clean(el.get("title") or (tnode.get_text(" ") if tnode else el.get_text(" ")))
        title = re.sub(r"\s*(첨부파일 있음|새 창 열림|훈련과정 정보)\s*$", "", title)
        title = re.sub(r"^(공지|NEW|new)\s+", "", title)
        row = container(el)
        row_text = clean(row.get_text(" ")) if row else ""
        if len(title) < 4:
            title = row_text[:80]
        if len(title) < 4:
            continue
        seen.add(url)
        out.append(item(source, title, url, first_date(row_text), row_text))
        if len(out) >= max_items:
            break
    return out


def detailbtn(source, ctx, max_items=40):
    """ptfol 계열(한국외대·숭실대 취업센터): a.detailBtn[data-params] + 카드 텍스트(신청기간/운영기간/교육기간)."""
    html = ctx["get"](source["url"])
    s = soup(html)
    seen, out = set(), []
    for a in s.select("a.detailBtn[data-params]"):
        m = re.search(r'"(?:encSddpbSeq|dataSeq)":"([0-9a-f]+)"', a.get("data-params") or "")
        if not m or m.group(1) in seen:
            continue
        row = container(a)
        row_text = clean(row.get_text(" ")) if row else ""
        tn = a.select_one(".tit") or (row.select_one(".tit, .text02, td.title") if row else None)
        title = clean(tn.get_text(" ")) if tn else clean(a.get_text(" "))
        title = re.sub(r"^(종료|모집중|마감|접수중)\s*", "", title)
        title = re.sub(r"^\d+\.\s*", "", title)
        if len(title) < 4:
            title = row_text[:80]
        if len(title) < 4:
            continue
        seen.add(m.group(1))
        out.append(item(source, title, source["url"] + "#" + m.group(1)[:12], first_date(row_text), row_text))
        if len(out) >= max_items:
            break
    return out
