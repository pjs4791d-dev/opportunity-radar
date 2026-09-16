"""JSON API 형 소스."""
import datetime, re
from .common import item, clean


def _d(s):
    if not s:
        return None
    s = str(s)
    m = re.match(r"(\d{4})-?(\d{2})-?(\d{2})", s)
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def pyxis(source, ctx, max_items=30):
    """도서관 Pyxis: data.list[].id/title/dateCreated"""
    j = ctx["get"](source["url"], json_body=True)
    out = []
    for x in (j.get("data") or {}).get("list", [])[:max_items]:
        url = source["detail_url"].format(id=x["id"]) if "{id}" in source.get("detail_url", "") else source["detail_url"]
        out.append(item(source, x.get("title"), url, _d(x.get("dateCreated")), org=source["name"].split(" ")[0]))
    return out


def sogang(source, ctx, max_items=30):
    j = ctx["get"](source["url"], json_body=True)
    out = []
    for x in (j.get("data") or {}).get("list", [])[:max_items]:
        out.append(item(source, x.get("title"), source["detail_url"].format(pkId=x["pkId"]), _d(x.get("regDate")), org="서강대학교"))
    return out


def hanyang_startup(source, ctx, max_items=30):
    j = ctx["get"](source["url"], json_body=True)
    out = []
    for x in (j.get("data") or {}).get("list", [])[:max_items]:
        body = re.sub(r"<[^>]+>", " ", x.get("content") or "")
        out.append(item(source, x.get("title"), source["detail_url"].format(contentId=x["contentId"]),
                        _d(x.get("regDate")), body, org="한양대 창업지원단"))
    return out
