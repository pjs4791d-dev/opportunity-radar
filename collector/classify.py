"""카테고리·우선순위 규칙."""
import re, datetime

CATS = [
    ("학사·행정", r"휴학|복학|수강|학점|폐강|졸업요건|졸업사정|등록금|납부|성적|계절학기|시간표|증명서|교직|이수의무|학사일정|수업조교|근로장학생|자퇴|전과|다전공 신청|복수전공|부전공|학위수여|앨범"),
    ("장학", r"장학|scholarship"),
    ("국제교류", r"교환학생|해외연수|어학연수|해외 파견|교환 프로그램|exchange|study abroad|파견|초청 장학"),
    ("공모전·해커톤", r"공모전|해커톤|경진대회|아이디어톤|데이터톤|챌린지|competition|경연"),
    ("채용·인턴", r"채용|인턴|\bRA\b|리서치 어시|공채|신입사원|일경험|현장실습|취업박람회|취업 ?특강|취업 ?스쿨|채용설명회|채용상담|직무 ?체험|Job Fair"),
    ("현장·기술직", r"목공|목수|가구|인테리어|도배|타일|용접|설비|전기|기능사|기술교육|훈련과정|건축시공|미장|조적|배관|자격취득"),
    ("창업·VC", r"창업|스타트업|\bVC\b|액셀러|데모데이|투자|\bIR\b|벤처|사업화|예비창업"),
    ("AI·테크", r"\bAI\b|인공지능|\bAX\b|데이터|LLM|딥러닝|머신러닝|\bSW\b|소프트웨어|코딩|클라우드|디지털|DX"),
    ("대외활동", r"서포터즈|홍보대사|기자단|봉사|파트너스|청년위원|모니터링단|앰배서더|동아리 모집"),
    ("세미나", r"세미나|포럼|콜로키움|학술|심포지엄|강연|발표회|컨퍼런스|토크|초청 특강|특강"),
    ("교육·부트캠프", r"교육|강좌|과정|부트캠프|아카데미|워크숍|워크샵|스쿨|캠프|튜터|멘토링|프로그램"),
]


def category(title, text=""):
    t = f"{title} {text}"
    for name, rx in CATS:
        if re.search(rx, t, re.I):
            return name
    return "공지"


SUBCATS = {
    "채용·인턴": [("리서치 RA", r"RA\b|리서치"), ("체험형 인턴", r"체험형"), ("채용연계형 인턴", r"채용연계|채용형"), ("인턴", r"인턴"), ("신입", r"신입|공채")],
    "현장·기술직": [("목공·가구제작", r"목공|목수|가구"), ("도배·건축마감", r"도배"), ("타일·건축마감", r"타일"), ("용접", r"용접"), ("설비·전기", r"설비|전기|에어컨")],
}


def subcategory(cat, title, text=""):
    for name, rx in SUBCATS.get(cat, []):
        if re.search(rx, f"{title} {text}", re.I):
            return name
    return "공고"


def priority(p, today):
    s = 35
    if p["eligibility"] == "yes":
        s += 15
    elif p["eligibility"] == "check":
        s += 3
    if p.get("dongguk_only"):
        s += 4
    s += {"finance": 10, "trades": 6, "campus": 0}.get(p["section"], 0)
    s += {"채용·인턴": 14, "창업·VC": 6, "AI·테크": 5, "공모전·해커톤": 7, "현장·기술직": 6, "국제교류": 6, "장학": 5,
          "교육·부트캠프": 3, "세미나": 2, "대외활동": 4, "공지": -12, "학사·행정": -25}.get(p["category"], 0)
    if re.search(r"금융|증권|투자|리서치|자산운용|은행|IB\b|애널리스트", p["title"]):
        s += 8
    if re.search(r"경력직|경력\s*\d+\s*년|경력사원|경력 채용|과장급|차장급|대리~|팀장|부장|박사|Ph\.?D|교수|전임교원|조교 채용|교직원|계약직 채용(?!.*인턴)", p["title"]):
        s -= 30   # 학생이 지원할 수 없는 경력·교직원 채용
    if re.search(r"신입|인턴|체험형|채용연계|\bRA\b|대학생|청년|공채|주니어|신규 채용", p["title"]):
        s += 8
    if re.search(r"학사|휴학|수강|등록금|졸업|폐강|성적|시험 일정|이수", p["title"]):
        s -= 15
    if p.get("deadline"):
        try:
            d = (datetime.date.fromisoformat(p["deadline"][:10]) - today).days
            if 0 <= d <= 3:
                s += 12
            elif d <= 7:
                s += 8
            elif d <= 21:
                s += 4
            elif d < 0:
                s -= 40
        except ValueError:
            pass
    if p.get("first_seen") == today.isoformat():
        s += 3
    return max(0, min(100, s))
