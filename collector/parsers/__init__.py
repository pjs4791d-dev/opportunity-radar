"""파서 레지스트리.

각 파서는 (source: dict, ctx) → list[dict] 를 돌려준다. 항목 dict 최소 필드:
  title, url, posted(date|None), org, text(제목 외 힌트 텍스트, 선택)
소스에 parser 가 지정돼 있지 않으면 config.PARSER_CONFIG → 없으면 generic.link_regex 기본값.
"""
from . import generic, dongguk, apis, special, config

REGISTRY = {
    "link_regex": generic.link_regex,
    "onclick_regex": generic.onclick_regex,
    "detailbtn": generic.detailbtn,
    "dongguk_article": dongguk.article_board,
    "pyxis": apis.pyxis,
    "sogang_api": apis.sogang,
    "hanyang_startup_api": apis.hanyang_startup,
    "seoul_youth": special.seoul_youth,
    "work24": special.work24,
    "kofia": special.kofia,
    "shinhan": special.shinhan,
    "yonsei_events": special.yonsei_events,
    "sitedu": special.sitedu,
    "text_lines": special.text_lines,
}


def resolve(source):
    """소스에 맞는 (parser_fn, options) 반환."""
    cfg = dict(config.PARSER_CONFIG.get(source["id"], {}))
    name = cfg.pop("parser", None) or source.get("parser") or "link_regex"
    return REGISTRY[name], cfg
