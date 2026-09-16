import re, datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

DATE_RE = re.compile(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})")


def soup(html):
    return BeautifulSoup(html, "html.parser")


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def first_date(text):
    m = DATE_RE.search(text or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def container(a):
    """앵커가 속한 목록 행(tr/li/article/div.item 류)."""
    for p in a.parents:
        if p.name in ("tr", "li", "article"):
            return p
        if p.name == "div" and p.get("class") and any(
            k in " ".join(p.get("class")) for k in ("item", "row", "list", "card", "post", "feed")
        ):
            return p
    return a.parent


def item(source, title, url, posted=None, text="", org=None, extra=None):
    d = {
        "title": clean(title),
        "url": url,
        "posted": posted,
        "org": org or source.get("org") or source["name"].split(" ")[0],
        "text": clean(text)[:600],
    }
    if extra:
        d.update(extra)
    return d
