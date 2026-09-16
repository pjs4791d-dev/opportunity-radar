# Opportunity Radar

서울 주요 대학·금융권·국비 기술훈련 공고를 자동으로 모아, 내가 참여할 수 있는 것만 걸러 보여주고 텔레그램으로 알려주는 개인용 대시보드.

## 폴더 구조

```
opportunity-radar/
├─ sources/sources.yaml   수집 대상 게시판 목록 (사람이 관리)
├─ collector/             수집기 (Python) — 3단계부터 작성
├─ data/
│  ├─ programs.json       화면이 읽는 최종 데이터
│  ├─ sources.json        화면의 "트래킹 소스" 목록 (추후 sources.yaml 에서 생성)
│  ├─ recurring.yaml      매년 반복 공고 (금융 캘린더용)
│  ├─ seen.json           이미 본 공고 ID
│  └─ errors.json         수집 실패 소스
├─ web/index.html         화면 (직접 설계한 피드형 UI — 마감 임박순 구간 목록, ★보관·숨기기, 금융 캘린더, 바로가기, 소스 상태)
└─ config.yaml            사용자·수집기 설정
```

## 실행 방법

### 로컬(맥)에서 한 번 수집

```bash
./run_local.sh --no-notify
```

- 처음 한 번: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- `.env.example` 을 `.env` 로 복사해 키를 넣으면 Claude 자격 판정·텔레그램 알림이 켜진다. 없으면 자동으로 건너뛴다.
- 일부만: `./run_local.sh --only dgu-,kofia --no-notify` / 목록만 빠르게: `.venv/bin/python collector/check_sources.py dgu-`

### GitHub Actions 자동 수집 (하루 2회 08:00·18:00 KST) + GitHub Pages

1. GitHub 에 저장소를 만들고 이 폴더를 push 한다.
2. 저장소 **Settings → Pages → Source** 를 `GitHub Actions` 로 바꾼다.
3. **Settings → Secrets and variables → Actions** 에 추가:
   - Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY`, (선택) `YOUTHCENTER_API_KEY`
   - Variables: `ANTHROPIC_MODEL` (비우면 `claude-haiku-4-5-20251001`)
4. **Actions 탭 → collect → Run workflow** 로 첫 실행. 끝나면 `https://<계정>.github.io/<저장소>/` 에서 화면이 뜬다.
   - 워크플로가 `data/*.json` 을 커밋하므로 맥에서 작업하기 전에 `git pull` 부터.

### 텔레그램 봇 만들기

1. 텔레그램에서 `@BotFather` → `/newbot` → 토큰 복사 (`TELEGRAM_BOT_TOKEN`).
2. 만든 봇에게 아무 메시지나 보낸 뒤 브라우저에서 `https://api.telegram.org/bot<토큰>/getUpdates` 를 열면 `"chat":{"id":123456789}` 가 보인다 (`TELEGRAM_CHAT_ID`).

## 로컬에서 화면 열기

`web/index.html` 을 더블클릭하면 브라우저가 JSON 읽기를 막는다. 프로젝트 폴더에서 아래를 실행한 뒤
http://localhost:8810/web/ 로 접속한다.

```bash
python3 -m http.server 8810
```

## programs.json 스키마

| 필드 | 설명 |
|---|---|
| `id` | 원문 URL 기반 해시 (초기 15건은 사람이 지은 id) |
| `title`, `org`, `url` | 제목·기관·원문 링크 |
| `section` | `campus` / `finance` / `trades` |
| `category`, `subcategory` | 분류 |
| `eligibility` | `yes` / `check` / `no` (`no` 는 화면에 안 뜸) |
| `eligibility_reason` | 판정 근거 원문 문구 |
| `dongguk_only` | 동국대 재학생 전용이면 true |
| `requires_card` | 국민내일배움카드 필요하면 true |
| `posted`, `deadline`, `event_date` | ISO 날짜, 모르면 null |
| `source_id` | `sources.yaml` 의 id. 초기 15건은 `manual-seed` |
| `first_seen` | 처음 발견한 날짜 (3일 이내면 NEW 표시) |
| `recurring` | 매년 반복 공고면 월 정보 (예 `"11-12"`) |
| `priority` | 추천 점수 |
| `also_at` | 중복 제거 시 합쳐진 다른 URL 목록 |
| `format`, `cost`, `keywords`, `benefit`, `description` | 기존 화면용 부가 정보 (수집기는 채우지 않을 수 있음) |

## 진행 상황

- [x] 1단계 뼈대 — 폴더 구조, 스키마, 화면 JSON 전환 (2026-09-16)
- [x] 2단계 소스 탐색 — `sources/sources.yaml` 220개 등록 (html 140 · api 9 · link 71) (2026-09-16)
- [x] 3단계 수집기 1차 — 동국대 16개 게시판, KOFIA, 고용24(서울·9개 키워드), 청년몽땅·서울청년센터 (2026-09-16)
- [x] 4단계 수집기 확장 — html/api 122개 소스에 파서 연결, 자격 판정(키워드 + Claude API), 중복 제거 (2026-09-16)
- [x] 5단계 GitHub Actions(하루 2회) · Pages 배포 · 텔레그램 알림 — 코드 완료, **저장소·Secrets 등록은 사용자가** (아래 실행 방법)
- [x] 6단계 화면 — 그룹/카드/동국대전용/신규/죽전 필터, 자격 근거, 확인 필요 접이식, 금융 연간 캘린더, 바로가기, 소스 상태 (2026-09-16)
- [x] 화면 재설계 — 처음 받은 HTML 을 버리고 폰 우선 피드형으로 새로 작성. ★보관·숨기기는 브라우저(localStorage)에만 저장 (2026-09-16)
- [ ] 7단계 (선택) 동국대 로그인 수집

## 아직 안 되는 것 / 알아둘 것

- **JS 렌더링 사이트**(NH·하나·교보·미래에셋·한투 채용, 스타트업플러스, 서울AI허브, SBA 공지, 청년일경험 공지 등)는 Playwright 가 필요해 아직 바로가기(`link`)다.
- **robots.txt 가 수집을 금지한 곳**(대학 도서관 Pyxis/KBoard 대부분, 국민대 경력개발지원단)은 규칙대로 수집하지 않고 바로가기로 뒀다.
- 고용24 훈련과정은 '모집중' 표시만 있고 접수 마감일이 목록에 없다 → 화면에 "마감일 확인"으로 뜬다. 훈련 시작일은 행사일 칸에 넣었다.
- `data/recurring.yaml` 은 비어 있다. 외국계 IB·CFA 리서치 챌린지처럼 매년 반복되는 일정을 직접 적으면 금융권 탭 '연간 캘린더'에 표시된다.
- `config.yaml` 의 `expected_graduation` 을 채우면 내일배움카드가 필요한 과정에 "카드 발급 가능 시점" 배지가 뜬다.
- 텔레그램 D-1 알림은 전체 공고 기준(★ 저장 연동은 추후).

## 소스 추가 방법

1. `sources/sources.yaml` 에 항목을 추가한다 (형식은 파일 상단 주석 참고). **실제로 열어 본 게시판 목록 URL만** 적고, 못 찾으면 `url: TODO`.
2. `.venv/bin/python collector/build_sources.py` 를 실행하면 `data/sources.json` 이 갱신되어 화면 '트래킹 소스' 탭에 나타난다.
3. 수집이 필요한 소스(`method: html|api`)는 3·4단계에서 `collector/parsers/` 에 파서를 붙인다.

대학별 등록 수: 동국대 17, 서울대 11, 연세대 9, 고려대 11, 서강대 8, 성균관대 7, 한양대 8, 중앙대 7, 경희대 8, 한국외대 7, 서울시립대 9, 홍익대 7, 건국대 9, 국민대 8, 숭실대 6, 세종대 7, 단국대 5

## TODO 소스 목록 (2단계 결과)

아래는 접속 실패·로그인 필요·JS 렌더링 등으로 게시판 URL을 확정하지 못한 소스다. 추측해서 넣지 않았다.

| ID | 이름 | 상태 |
|---|---|---|
| `yonsei-lifelong` | 연세대 미래교육원 | URL 미확인 — 사이트 접속 실패(타임아웃). 재확인 필요 |
| `sogang-career` | 서강대 취업지원센터 | URL 미확인 — sgcareer.sogang.ac.kr 접속 실패. 실제 주소 재확인 |
| `sogang-startup` | 서강대 창업지원단 | URL 미확인 — startup.sogang.ac.kr 접속 실패. 실제 주소 재확인 |
| `hanyang-career` | 한양대 취업지원 (커리어개발센터) | URL 미확인 — career/job.hanyang.ac.kr 접속 실패. 실제 주소 재확인 |
| `khu-biz` | 경희대 경영대학 공지 | URL 미확인 — cba/khubs 도메인 접속 실패. 실제 주소 재확인 |
| `hongik-biz` | 홍익대 경영대학 | URL 미확인 — 단과대 도메인 접속 실패. 대학공지에 통합 게시되는지 확인 |
| `sejong-startup` | 세종대 창업지원단 | URL 미확인 — startup.sejong.ac.kr 접속 실패. 실제 주소 재확인 |
| `kiwoom-recruit` | 키움증권 채용 | URL 미확인 — kiwoom.com/h/recruit 오류페이지. 실제 채용 사이트 URL 재확인 |
| `daishin-recruit` | 대신증권 채용 | URL 미확인 —  |
| `meritz-recruit` | 메리츠증권 채용 | URL 미확인 —  |
| `samsung-am` | 삼성자산운용 채용 | URL 미확인 — 운용사 채용은 KOFIA 회원사 채용안내에 대부분 게시됨 |
| `kim-am` | 한국투자신탁운용 채용 | URL 미확인 —  |
| `ksfc-recruit` | 한국증권금융 채용 | URL 미확인 — ksfc.co.kr 접속 실패 |
| `cfa-research-challenge` | CFA Institute Research Challenge | URL 미확인 — 연간 캘린더(recurring.yaml)에 등록. CFA Society Korea 공고 URL 재확인 |
| `mirae-foundation` | 미래에셋박현주재단 장학 | URL 미확인 — 도메인 접속 실패. 재확인 |
| `foreign-ib-careers` | 외국계 IB 서울 오피스 커리어 페이지 | URL 미확인 — recurring.yaml 연간 캘린더로 관리 |
| `nuch-open` | 한국전통문화대학교 공개 과정 | URL 미확인 — nuch.ac.kr 접속 실패. 재확인 |
| `snu-lifelong` | 서울대 평생교육원 | 바로가기로만 등록 — 강좌 목록 페이지 URL 미확인 (TODO) |
| `hanyang-library` | 한양대 백남학술정보관 | 바로가기로만 등록 — 공지 게시판 URL 미확인 (TODO) |
| `cau-library` | 중앙대 학술정보원 | 바로가기로만 등록 — Angular SPA. 공지 API 미확인 (TODO) |
| `uos-biz` | 서울시립대 경영대학 | 바로가기로만 등록 — SSO 리다이렉트로 공지 목록 URL 미확인 (TODO) |
| `uos-lifelong` | 서울시립대 평생교육원 | 바로가기로만 등록 — JS 앱(Athena). 강좌 목록 URL 미확인 (TODO) |
| `kookmin-library` | 국민대 성곡도서관 | 바로가기로만 등록 — Pyxis 이지만 게시판 ID 1 없음 → 게시판 ID 확인 필요 (TODO) |
| `ssu-library` | 숭실대 중앙도서관 | 바로가기로만 등록 — 공지 게시판 URL 미확인 (TODO) |
| `dku-youngwoong` | 단국대 YOUNG熊STORY (취창업·비교과) | 바로가기로만 등록 — 세션 기반. 목록 열람 가능 여부 재확인 (TODO) |
| `dku-lifelong` | 단국대 평생교육원(죽전) | 바로가기로만 등록 — EUC-KR 구형 사이트. 강좌 목록 URL 미확인 (TODO) |
| `kmooc` | K-MOOC | 바로가기로만 등록 — 신규 강좌 목록 URL 미확인(/view/course/list 는 500). 메인에 /view/course/detail/{id} 카드 노출 |
| `startup-plus` | 스타트업플러스 (서울시 통합 창업 플랫폼) 지원사업 | 바로가기로만 등록 — Vue 앱. 목록 API 미확인 |
| `american-center-korea` | 주한미국대사관 American Center Korea | 바로가기로만 등록 — American Center 전용 페이지 404. 행사 목록 URL 미확인 (TODO) |
| `british-council` | 주한영국문화원 | 바로가기로만 등록 — 접속 실패(타임아웃). 재확인 |
| `krx-recruit` | 한국거래소 채용 | 바로가기로만 등록 — 메인이 JS 앱(973B). 채용 페이지 URL 미확인 (TODO) |
| `cwma-training` | 건설근로자공제회 건설기능인 양성훈련 | 바로가기로만 등록 — 건설e음 '사업 및 훈련기관 안내'. 훈련생 모집 공고 게시판 URL 미확인 (TODO). 훈련기관은 매년 11~12월 공모 → 연초 공고 집중 |
| `nbedu` | 서울시 기술교육원 남부캠퍼스 (군포) | 바로가기로만 등록 — 접속 실패(타임아웃). 통합 사이트(sitedu) 원서접수로 대부분 커버 |
| `work-learning-dual` | 일학습병행 과정 (고용24) | 바로가기로만 등록 — 고용24 '직업능력개발 > 일학습병행과정' 메뉴. fn_goPageUrl 로만 진입 → 직접 URL 미확인 (TODO) |

### 2단계에서 알게 된 것

- **한 곳에서 여러 대학을 커버하는 소스**: 서울캠퍼스타운 포털 `캠타프로그램`(`campustown-programs`)은 17개 대학 캠퍼스타운 공고를 `[OO대학교 캠퍼스타운]` 접두어로 한 게시판에 모아 준다. 대학별 캠퍼스타운 사이트를 따로 찾을 필요가 없다.
- **JSON API 가 있는 곳**: 서강대(Nuxt `BbsData/boardList`), 한양대 창업지원단(`/api/board/content`), 도서관 Pyxis(`/pyxis-api/1/bulletin-boards/1/bulletins` — 동국·성균관·외대·건국). 온통청년 API 는 회원 키 승인이 필요하다.
- **로그인이 필요한 취업센터**: 서울대·연세대·고려대·성균관대·중앙대·서울시립대 취업 시스템은 목록도 로그인 후 열람 → `link`. 반면 국민대(지역청년 프로그램), 숭실대(청년고용서비스), 한국외대(비교과 목록), 건국대(소식)는 로그인 없이 열람 가능.
- **SSO 우회 파라미터**: 서울시립대는 `?identified=anonymous`, 건국대는 `index.do` 대신 `subview.do` 로 직접 접근하면 된다.
- **고용24**: 훈련과정 검색이 GET URL 로 동작한다(서울 `area=11`, 키워드별). 상세도 GET 200. 오픈API 안내 페이지는 405.
- **잡알리오**: `work_type=R1060`(체험형)·`R1070`(채용형) GET 필터가 동작한다.
- **증권사 채용 페이지**: 신한(서버 렌더)·KB(greetinghr)만 html 수집 가능. NH·하나·교보(recruiter.co.kr), 미래에셋, 한투는 JS 렌더링이라 Playwright 가 필요 → 일단 `link`. 운용사 채용은 KOFIA 회원사 채용안내가 대부분 커버한다.
