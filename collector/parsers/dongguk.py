"""동국대 대표 홈페이지 게시판 (/article/{BOARD}/list): li > a[onclick=goDetail(seq)]"""
import re
from .common import soup, clean, first_date, item

GO = re.compile(r"goDetail\((\d+)\)")


def article_board(source, ctx, max_items=40):
    html = ctx["get"](source["url"])
    s = soup(html)
    out = []
    for a in s.select("div.board_list li a[onclick]"):
        m = GO.search(a["onclick"])
        if not m:
            continue
        url = source["detail_url"].format(seq=m.group(1))
        tit = a.select_one("p.tit")
        title = clean(tit.get_text(" ")) if tit else clean(a.get_text(" "))
        title = re.sub(r"^공지\s*", "", title)
        info = a.select_one("div.info")
        posted = first_date(info.get_text(" ")) if info else None
        out.append(item(source, title, url, posted, org="동국대학교"))
        if len(out) >= max_items:
            break
    return out
