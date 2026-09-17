"""사이트 전용 파서."""
import re, datetime
from urllib.parse import urljoin
from .common import soup, clean, first_date, container, item


def seoul_youth(source, ctx, max_items=40):
    """청년몽땅정보통 / 서울청년센터: div.feed-item a[onclick=goView('id')]"""
    html = ctx["get"](source["url"])
    s = soup(html)
    out = []
    for fi in s.select("div.feed-item, div.gallery-list-st1 div.list"):
        a = fi.select_one("a[onclick]")
        m = a and re.search(r"goView\('(\d+)'\)", a["onclick"])
        if not m:
            continue
        name = fi.select_one(".name, strong.ti")
        cate = fi.select_one(".cate, .cate2")
        state = fi.select_one(".state, .cate1")
        title = clean(name.get_text(" ") if name else a.get_text(" "))
        title = re.sub(r"\.{3,}\d+$", "", title)  # 이미지 파일번호 꼬리 제거
        org = "서울특별시"
        mo = re.match(r"^(?:\[[^\]]+\]\s*)?(.{2,25}?)\s*[<＜]", title)
        if mo:
            org = mo.group(1).strip()
        out.append(item(source, title, source["detail_url"].format(id=m.group(1)), None,
                        f"{cate.get_text() if cate else ''} {state.get_text() if state else ''}", org=org,
                        extra={"category_hint": clean(cate.get_text()) if cate else "", "state": clean(state.get_text()) if state else ""}))
        if len(out) >= max_items:
            break
    return out


def seoul_youth_detail(text):
    """상세 본문에서 신청기간/진행일정/대상 구조화 텍스트."""
    t = clean(text)
    out = {}
    for k, kw in (("apply", "신청기간"), ("event", "진행일정"), ("target", "대상"), ("org", "담당기관")):
        m = re.search(kw + r"\s*(.{0,60})", t)
        if m:
            out[k] = m.group(1)
    return out


def kofia(source, ctx, max_items=300, max_pages=25, days=35):
    """KOFIA 채용안내: tr > td(번호) td(회원사) td.left(제목, a[href=view.do?seq=]) td(파일) td.num(작성일).
    제목 앵커 HTML 이 깨져 있어(span 안에서 a 시작) td 텍스트를 쓴다.
    한 페이지 10건. 접수기간이 한 달 넘는 공고가 많아 게시일이 days 일 이전이 나올 때까지 페이지를 넘긴다(?page=N)."""
    import datetime as _dt
    cutoff = _dt.date.today() - _dt.timedelta(days=days)
    out, seen_seq = [], set()
    for page in range(1, max_pages + 1):
        html = ctx["get"](source["url"] + ("" if page == 1 else f"?page={page}"))
        rows = _kofia_rows(source, soup(html), seen_seq)
        if not rows:
            break
        out.extend(rows)
        if len(out) >= max_items or any(r["posted"] and r["posted"] < cutoff for r in rows):
            break
    return out[:max_items]


def _kofia_rows(source, s, seen_seq):
    out = []
    for tr in s.select("tr"):
        a = tr.select_one("a[href*='view.do?seq=']")
        if not a:
            continue
        m = re.search(r"seq=(\d+)", a["href"])
        tds = tr.find_all("td")
        if not m or len(tds) < 3:
            continue
        if m.group(1) in seen_seq:
            continue
        seen_seq.add(m.group(1))
        org = clean(tds[1].get_text(" "))
        title = clean(tds[2].get_text(" ")).replace(" new", "").strip()
        posted = first_date(tr.get_text(" "))
        if len(title) < 4:
            continue
        out.append(item(source, title, source["detail_url"].format(seq=m.group(1)), posted, f"{org} {title}", org=org or "금융투자협회 회원사"))
    return out


def shinhan(source, ctx, max_items=40):
    html = ctx["get"](source["url"])
    s = soup(html)
    out = []
    for li in s.select("li.recruit_list__item"):
        tit = li.select_one(".recruit_list__tit")
        info = li.select_one(".recruit_list__info")
        date = li.select_one(".recruit_list__date")
        if not tit:
            continue
        title = clean(tit.get_text(" "))
        text = clean(f"{info.get_text(' ') if info else ''} 마감 {date.get_text(' ') if date else ''}")
        out.append(item(source, title, source["url"] + "#" + re.sub(r"\W+", "-", title)[:40], None, text, org="신한투자증권"))
        if len(out) >= max_items:
            break
    return out


def work24(source, ctx, max_items=30):
    """고용24 훈련과정 검색: keywords 별로 검색. div.list[data-tracseid] 카드에서 기관·기간·지역·부담금 추출."""
    import datetime as _dt
    from urllib.parse import quote
    today = _dt.date.today()
    base = source["url"].replace("{today}", today.strftime("%Y%m%d")).replace("{today+1y}", today.replace(year=today.year + 1).strftime("%Y%m%d"))
    out, seen = [], set()
    for kw in source.get("keywords") or ["목공"]:
        html = ctx["get"](base.replace("{keyword}", quote(kw)))
        s = soup(html)
        n = 0
        for card in s.select("div.list[data-tracseid]"):
            for tt in card.select(".box_tooltip, script, style"):
                tt.decompose()
            a = card.select_one("a[onclick*='fn_viewTracseInfo']")
            m = a and re.search(r"fn_viewTracseInfo\('([^']+)','([^']+)','([^']+)','([^']+)'", a["onclick"])
            if not m:
                continue
            title = clean(re.sub(r"\s*훈련과정 정보 새 창 열림$", "", a.get("title") or a.get_text(" ")))
            if kw not in title and kw not in clean(card.get_text(" "))[:200]:
                continue  # 전문검색 오탐(예: '목공' → 토목) 제거
            durl = source["detail_url"].format(tracseId=m.group(1), tracseTme=m.group(2), crseTracseSe=m.group(3), trainstCstmrId=m.group(4))
            if durl in seen:
                continue
            inst_a = card.select_one("a[onclick*='fn_viewTrainstInfo']")
            inst = clean(re.sub(r"\s*훈련기관정보 새 창 열림$", "", inst_a.get("title") or inst_a.get_text(" "))) if inst_a else ""
            period = card.select_one(".time")
            period = clean(period.get_text(" ")) if period else ""
            site = card.select_one(".site")
            site = clean(site.get_text(" ")) if site else ""
            site = re.sub(r"\(.*?\)", "", site).strip()
            hours = [clean(x.get_text(" ")) for x in card.select(".info") if "시간" in x.get_text()]
            state = card.select_one(".right_btn_area .t3_sb")
            state = clean(state.get_text()) if state else ""
            pay = card.select_one(".right_btn_area .mb8")
            pay = clean(pay.get_text()) if pay else ""
            tags = " ".join(clean(x.get_text()) for x in card.select(".hashtag_wrap .clr_blue"))
            text = f"{state} 훈련기간 {period} {hours[0] if hours else ''} {site} 본인부담 {pay} {tags}"
            seen.add(durl)
            out.append(item(source, title, durl, None, text, org=f"고용24 · {inst}" if inst else "고용24",
                            extra={"keyword": kw, "requires_card": True, "state": state, "cost": pay, "location": site, "period": period}))
            n += 1
            if n >= max_items:
                break
    return out


def yonsei_events(source, ctx, max_items=40):
    html = ctx["get"](source["url"])
    s = soup(html)
    out = []
    for tit in s.select("p.eventTit"):
        title = clean(tit.get_text(" "))
        if len(title) < 4:
            continue
        blk = tit
        for p in tit.parents:
            if p.name in ("li", "dl", "div") and len(clean(p.get_text(" "))) > len(title) + 20:
                blk = p
                break
        text = clean(blk.get_text(" "))
        out.append(item(source, title, source["url"] + "#" + re.sub(r"\W+", "-", title)[:40], None, text, org="연세대학교"))
        if len(out) >= max_items:
            break
    return out


def sitedu(source, ctx, max_items=20):
    """서울시 기술교육원 통합 모집 페이지: 캠퍼스별 모집일정 + 청년 특화 과정 이름을 항목으로."""
    html = ctx["get"](source["url"])
    t = clean(re.sub(r"<!--.*?-->", " ", html, flags=re.S))
    t = clean(re.sub(r"<[^>]+>", " ", t))
    out = []
    for campus in ("중부캠퍼스", "북부캠퍼스", "동부캠퍼스", "남부캠퍼스"):
        m = re.search(campus + r"\s*:\s*(\d{1,2}월\s*\d{1,2}일\([월화수목금토일]\)\s*~\s*\d{1,2}월\s*\d{1,2}일\([월화수목금토일]\))", t)
        sched = m.group(1) if m else ""
        m2 = re.search(campus + r".*?청년 특화 과정\s*(.*?)(?=(?:중부|북부|동부|남부)캠퍼스|일경험|$)", t)
        youth = clean(m2.group(1))[:120] if m2 else ""
        if not (sched or youth):
            continue
        title = f"서울시 기술교육원 {campus} 모집" + (f" · 청년특화: {youth}" if youth else "")
        out.append(item(source, title, source["url"] + "#" + campus, None, f"모집 일정 {sched}", org="서울특별시 기술교육원"))
    return out[:max_items]


def text_lines(source, ctx, pattern, max_items=30):
    """페이지 텍스트에서 정규식으로 항목 뽑기 (예비용)."""
    html = ctx["get"](source["url"])
    t = clean(re.sub(r"<[^>]+>", " ", html))
    out = []
    for m in re.finditer(pattern, t):
        out.append(item(source, m.group(0)[:100], source["url"], None, m.group(0)))
        if len(out) >= max_items:
            break
    return out
