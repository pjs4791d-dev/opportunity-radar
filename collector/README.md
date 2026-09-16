# collector

```
run.py            전체 수집 진입점  (.venv/bin/python collector/run.py [--only id접두어,...] [--no-detail] [--no-notify] [--limit N])
check_sources.py  소스별 목록 파싱만 빠르게 점검 (상세 안 열음)
build_sources.py  sources.yaml → data/sources.json, recurring.yaml → recurring.json
fetch.py          HTTP: User-Agent, 도메인별 2초 간격, robots.txt 준수, 재시도, curl 폴백
dates.py          제목·본문에서 마감일/행사일 추출 (못 찾으면 None)
eligibility.py    참여 자격 판정 (키워드 → Claude API → check)
dedupe.py         제목 유사도 0.85 + 마감일 동일 → 중복 합치기 (also_at)
classify.py       카테고리·우선순위 규칙
notify.py         텔레그램 (신규 yes 공고 / D-3·D-1 / 3회 연속 실패)
parsers/
  config.py       소스 id → 파서 이름 + 옵션. 지정 없으면 generic.link_regex(기본 링크 패턴)
  generic.py      link_regex(상세 링크 패턴), onclick_regex(onclick 인자 → 상세 URL), detailbtn(ptfol 계열)
  dongguk.py      동국대 대표 홈페이지 게시판
  apis.py         Pyxis(도서관) / 서강대 / 한양대 창업지원단 JSON
  special.py      청년몽땅·KOFIA·신한·고용24·연세대 행사·서울시 기술교육원
```

## 새 소스에 파서 붙이기

1. `check_sources.py <id>` 로 0건이면 목록 페이지의 상세 링크 모양을 본다.
2. 링크에 규칙이 있으면 `config.py` 에 `{"patterns": [r"..."]}`, onclick 이면 `{"parser": "onclick_regex", "onclick": r"fn\('(\d+)'\)", "detail": "https://.../view?id={0}"}`.
3. 그래도 안 되면 `special.py` 에 함수를 만들고 `__init__.py` REGISTRY 에 등록.

## 데이터 파일

- `data/programs.json` 화면용. `eligibility: no` 는 저장하지 않음.
- `data/seen.json`  {id: {url,title,first_seen,last_seen,eligibility,...}} — 신규 판별·자격 판정 캐시. 지우면 전부 신규로 다시 잡는다.
- `data/source_status.json` 소스별 마지막 성공 시각·연속 실패 횟수 (sources.json 에 합쳐져 화면 표시).
- `data/errors.json` 실패 소스 목록.
