"""텔레그램 알림 (명세서 7장). 토큰·채팅ID 는 환경변수 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID."""
import os, datetime, requests

SECTION = {"campus": "대학·청년", "finance": "금융", "trades": "기술"}


def _send(text):
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("(텔레그램 미설정 — 알림 생략)")
        return False
    for chunk in _chunks(text, 3800):
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                          json={"chat_id": chat, "text": chunk, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=20)
        if r.status_code != 200:
            print("텔레그램 전송 실패:", r.text[:200])
            return False
    return True


def _chunks(text, n):
    lines, buf = text.split("\n"), ""
    for ln in lines:
        if len(buf) + len(ln) + 1 > n:
            yield buf
            buf = ""
        buf += ln + "\n"
    if buf:
        yield buf


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _dday(p, today):
    if not p.get("deadline"):
        return "마감일 확인"
    d = (datetime.date.fromisoformat(p["deadline"][:10]) - today).days
    md = p["deadline"][5:10].replace("-", "/").lstrip("0").replace("/0", "/")
    return f"마감 {md} (D-{d})" if d > 0 else (f"마감 {md} (오늘)" if d == 0 else f"마감 {md}")


def line(p, today):
    return f"[{SECTION.get(p['section'], '')}] {_esc(p['org'])} {_esc(p['title'])} · {_dday(p, today)}\n<a href=\"{p['url']}\">원문</a>"


def send_digest(programs, new_items, errors, today):
    parts = []
    new_yes = [p for p in new_items if p["eligibility"] == "yes"]
    if new_yes:
        parts.append(f"<b>🆕 신규 공고 {len(new_yes)}건</b> ({today})")
        for sec in ("finance", "campus", "trades"):
            grp = [p for p in new_yes if p["section"] == sec]
            if not grp:
                continue
            parts.append(f"\n<b>— {SECTION[sec]} ({len(grp)})</b>")
            for p in sorted(grp, key=lambda x: -x["priority"])[:25]:
                parts.append(line(p, today))
            if len(grp) > 25:
                parts.append(f"… 외 {len(grp) - 25}건")
    d1 = [p for p in programs if p.get("deadline") and p["eligibility"] == "yes"
          and (datetime.date.fromisoformat(p["deadline"][:10]) - today).days in (1, 3)]
    if d1:
        parts.append(f"\n<b>⏰ 마감 임박 (D-3 / D-1) {len(d1)}건</b>")
        for p in sorted(d1, key=lambda x: x["deadline"])[:20]:
            parts.append(line(p, today))
    bad = [e for e in errors if e.get("fail_count", 0) >= 3]
    if bad:
        parts.append(f"\n<b>⚠️ 3회 이상 연속 실패 소스 {len(bad)}개</b>")
        for e in bad[:15]:
            parts.append(f"• {_esc(e['name'])}: {_esc(e['error'][:60])}")
    if not parts:
        print("(알릴 내용 없음)")
        return
    _send("\n".join(parts))
