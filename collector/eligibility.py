"""참여 자격 판정 (명세서 5-1).

판정 순서
1. default_scope=dongguk → yes. 원문에 재학생/본교생 → dongguk_only.
2. default_scope=public  → yes. 나이·거주지 조건 문구를 reason 에 기록.
3. default_scope=other_univ → 제외 키워드 → no / 허용 키워드 → yes / 둘 다 없으면 Claude API → 애매하면 check.
근거 문구는 반드시 원문에서 그대로 따온다.
"""
import os, re, json

EXCLUDE = ["본교생", "본교 재학생", "재학생에 한함", "재학생만", "재학생 대상", "학부생에 한함", "본교 학부생",
           "교내 구성원", "포털 로그인 후 신청", "포털 로그인", "우리 대학 재학생", "우리대학 재학생", "본교 학생",
           "본교 소속", "재학생(휴학생 포함)에 한", "학생회원 전용"]
ALLOW = ["누구나", "타교생", "타 대학", "타대생", "타 학교", "외부인", "일반인", "소속 무관", "소속에 관계없이",
         "대학생이면", "전국 대학생", "관심 있는 분", "관심있는 분", "청년 누구나", "지역 청년", "지역청년", "서울시민",
         "서울 거주", "만 19", "만 18", "19~39세", "19세~39세", "19세 이상", "재학생 및 일반인", "외부 참여", "누구든지"]
DGU_ONLY = ["재학생", "본교생", "본교 학생", "우리 대학", "우리대학", "학부생", "재학 중인 학생"]
COND = re.compile(r"(만\s?\d{2}\s?[~∼-]\s?\d{2}\s?세|\d{2}\s?[~∼-]\s?\d{2}\s?세|\d{2}세\s?(이상|이하|미만)|서울\s?(시민|거주|생활권)|[가-힣]+구\s?(거주|주민)|미취업|졸업생|재학생|휴학생|대학생|청년)")


def _snippet(text, kw, width=44):
    i = text.find(kw)
    if i < 0:
        return kw
    s = max(0, i - width // 2)
    e = min(len(text), i + len(kw) + width // 2)
    if s > 0:
        s = text.rfind(" ", 0, s + 1) + 1 if text.rfind(" ", 0, s + 1) >= 0 else s
    if e < len(text):
        e2 = text.find(" ", e)
        e = e2 if 0 <= e2 - e < 12 else e
    return ("…" if s > 0 else "") + text[s:e].strip() + ("…" if e < len(text) else "")


def judge(scope, title, body, api_client=None, model=None):
    """→ dict(eligibility, eligibility_reason, dongguk_only)"""
    text = re.sub(r"\s+", " ", f"{title} {body or ''}")
    if scope == "dongguk":
        only = next((k for k in DGU_ONLY if k in text), None)
        return {"eligibility": "yes", "eligibility_reason": _snippet(text, only) if only else "동국대 공고",
                "dongguk_only": bool(only)}
    if scope == "public":
        m = COND.search(text)
        return {"eligibility": "yes", "eligibility_reason": _snippet(text, m.group(0)) if m else "공개 공고",
                "dongguk_only": False}
    # other_univ
    ex = next((k for k in EXCLUDE if k in text), None)
    if ex:
        return {"eligibility": "no", "eligibility_reason": _snippet(text, ex), "dongguk_only": False}
    al = next((k for k in ALLOW if k in text), None)
    if al:
        return {"eligibility": "yes", "eligibility_reason": _snippet(text, al), "dongguk_only": False}
    if api_client and body and len(body) > 40:
        r = ask_claude(api_client, model, title, body)
        if r:
            return {"eligibility": r["eligibility"], "eligibility_reason": r["reason"], "dongguk_only": False}
    return {"eligibility": "check", "eligibility_reason": "소속 제한 문구 없음 — 원문 확인", "dongguk_only": False}


PROMPT = """다음은 어느 대학 게시판에 올라온 공고입니다. 동국대학교 재학생(타 대학 학생)이 참여할 수 있는지 판정하세요.
- 해당 대학 소속만 가능하면 "no", 타교생·일반인·전국 대학생 등 외부 참여가 명시되면 "yes", 판단 근거가 없거나 애매하면 "check".
- reason 에는 판정 근거가 된 원문 문장을 그대로(30자 이내로 잘라서) 넣으세요. 원문에 없는 말을 지어내지 마세요.
JSON 한 줄로만 답하세요: {{"eligibility": "yes|check|no", "reason": "근거 문구"}}

제목: {title}
본문:
{body}"""


def ask_claude(client, model, title, body):
    try:
        msg = client.messages.create(
            model=model, max_tokens=200,
            messages=[{"role": "user", "content": PROMPT.format(title=title, body=body[:2500])}],
        )
        txt = "".join(getattr(b, "text", "") for b in msg.content)
        m = re.search(r"\{.*\}", txt, re.S)
        r = json.loads(m.group(0))
        if r.get("eligibility") in ("yes", "check", "no"):
            return {"eligibility": r["eligibility"], "reason": (str(r.get("reason", ""))[:70] or "근거 미기재") + " (AI 판정)"}
    except Exception:
        return None
    return None


def make_client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None, None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=key), os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    except Exception:
        return None, None
