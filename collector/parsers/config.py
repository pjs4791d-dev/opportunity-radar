"""소스별 파서 지정. 없으면 generic.link_regex(기본 패턴).

키: sources.yaml 의 id. 값: {"parser": 이름, ...파서 옵션}
"""
DGU = {"parser": "dongguk_article"}
KHU_VIEW = {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "{base}?boardId={0}"}

PARSER_CONFIG = {
    # ── 동국대 ──
    "dgu-general": DGU, "dgu-haksa": DGU, "dgu-scholarship": DGU, "dgu-intl": DGU, "dgu-events": DGU,
    "dgu-library": {"parser": "pyxis"},
    "dgu-dvic-notice": {"patterns": [r"/dvic5_7/\d+"]},
    "dgu-dvic-programs": {"patterns": [r"/dvic2_2/\d+"]},
    "dgu-deep-notice": {"patterns": [r"/notice/[^/?]+/?$"], "exclude": r"page=|bo_table"},
    "dgu-intern": {"patterns": [r"STU_NOTICE/detail/\d+"]},
    "dgu-work-scholarship": {"patterns": [r"/notice/detail/\d+"]},
    "dgu-english": {"patterns": [r"/notice1/detail/\d+"]},
    "dgu-business": {"patterns": [r"/job/detail/\d+"]},
    "dgu-econ": {"patterns": [r"/notice/detail/\d+"]},
    "dgu-edulife": {"parser": "onclick_regex", "onclick": r"location\.href='(/ngrade/site/article/24/detail/\d+)'", "detail": "https://edulife.dongguk.edu{0}"},
    "dgu-campustown-seoul": {"patterns": [r"/university_news/\d+"]},
    # ── 서울대 ──
    "snu-general": {"patterns": [r"bbsidx=\d+"]}, "snu-events": {"patterns": [r"bbsidx=\d+"]},
    "snu-public-lecture": {"patterns": [r"bbsidx=\d+"]}, "snu-cba": {"patterns": [r"bbsidx=\d+"]},
    "snu-startup-events": {"patterns": [r"wr_id=\d+"]}, "snu-startup-notice": {"patterns": [r"wr_id=\d+"]},
    "snu-library": {"patterns": [r"uid=\d+"]},
    # ── 연세대 ──
    "yonsei-events": {"parser": "yonsei_events"},
    "yonsei-general": {"patterns": [r"artclView\.do"]},
    # ── 고려대 ──
    "korea-general": {"parser": "onclick_regex", "onclick": r"jf_view\('(\d+)','(\d+)','ko'\)", "detail": "https://www.korea.ac.kr/portalBoard/ko/{1}/{0}/portalBoardView.do"},
    "korea-student-events": {"parser": "onclick_regex", "onclick": r"jf_view\('(\d+)','(\d+)','ko'\)", "detail": "https://www.korea.ac.kr/portalBoard/ko/{1}/{0}/portalBoardView.do"},
    "korea-startup": {"parser": "onclick_regex", "onclick": r"programView\.do\?seq=(\d+)", "detail": "https://kustartup.korea.ac.kr/program/programView.do?seq={0}"},
    "korea-campustown": {"patterns": [r"wr_id=\d+"]},
    "korea-library": {"patterns": [r"uid=\d+"]},
    # ── 서강대 ──
    "sogang-general": {"parser": "sogang_api"}, "sogang-student": {"parser": "sogang_api"}, "sogang-haksa": {"parser": "sogang_api"},
    # ── 성균관대 ──
    "skku-library": {"parser": "pyxis"},
    # ── 한양대 ──
    "hanyang-startup": {"parser": "hanyang_startup_api"},
    "hanyang-general": {"patterns": [r"entryId=\d+"], "exclude": r"cur=|Type="},
    # ── 경희대 ──
    "khu-general": {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "https://www.khu.ac.kr/kor/user/bbs/BMSR00040/view.do?boardId={0}&menuNo=200316"},
    "khu-startup-external": {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "https://startup.khu.ac.kr/startup_kor/user/bbs/BMSR00040/view.do?boardId={0}&menuNo=15200026"},
    "khu-startup-notice": {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "https://startup.khu.ac.kr/startup_kor/user/bbs/BMSR00040/view.do?boardId={0}&menuNo=15200019"},
    "khu-econ": {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "https://econ.khu.ac.kr/econ/user/bbs/BMSR00040/view.do?boardId={0}&menuNo=4400060"},
    "khu-lifelong": {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "https://ice.khu.ac.kr/ice/user/bbs/BMSR00040/view.do?boardId={0}&menuNo=5700036"},
    # ── 한국외대 ──
    "hufs-library": {"parser": "pyxis"},
    "hufs-job-programs": {"parser": "detailbtn"},
    "ssu-job-programs": {"parser": "detailbtn"}, "ssu-job-youth": {"parser": "detailbtn"},
    "korea-biz": {"patterns": [r"notice_view\.html\?no=\d+"]},
    "cau-biz": {"patterns": [r"_view\.php\?bbsIdx=\d+"]},
    "hongik-career": {"patterns": [r"/career/boardview/\d+/\d+"]},
    "kookmin-startup": {"patterns": [r"^\./\d+$"]}, "kookmin-biz": {"patterns": [r"^\./\d+$"]},
    "kita-notice": {"parser": "onclick_regex", "onclick": r"goDetailPage\('(\d+)'\)", "detail": "https://www.kita.net/board/notice/noticeDetail.do?postIndex={0}"},
    "fulbright-news": {"patterns": [r"fulbright\.or\.kr/\d{4}-[a-z0-9-]+/$"]},
    "jbedu-notice": {"parser": "onclick_regex", "onclick": r"goBoardView\('/user/nd29455\.do','View','(\d+)'\)", "detail": "https://www.jbedu.or.kr/user/nd29455.do#post-{0}"},
    "kopo-jungsu-hitech": {"parser": "onclick_regex", "onclick": r"fn_board_detail\('(\d+)'\)", "detail": "https://www.kopo.ac.kr/jungsu/board.do?menu=14157#post-{0}"},
    "kopo-kangseo-notice": {"parser": "onclick_regex", "onclick": r"fn_board_detail\('(\d+)'\)", "detail": "https://www.kopo.ac.kr/kangseo/board.do?menu=317#post-{0}"},
    "hanyang-biz": {"parser": "onclick_regex", "onclick": r"BbsPortlet_viewMessage\((\d+)", "detail": "https://biz.hanyang.ac.kr/-28#msg-{0}"},
    # ── 서울시립대 ──
    "uos-general": {"parser": "onclick_regex", "onclick": r"fnView\('\d+',\s*'(\d+)'\)", "detail": "https://www.uos.ac.kr/korNotice/view.do?list_id=FA1&seq={0}&identified=anonymous"},
    "uos-startup-notice": {"parser": "onclick_regex", "onclick": r"fnView\('\d+',\s*'(\d+)'\)", "detail": "https://www.uos.ac.kr/korColumn/view.do?list_id=FA35&seq={0}&identified=anonymous"},
    "uos-startup-center": {"parser": "onclick_regex", "onclick": r"view\('(\d+)'", "detail": "http://startup.uos.ac.kr/cm/cm-1.php?mode=view&idx={0}"},
    # ── 건국대 ──
    "konkuk-library": {"parser": "pyxis"},
    "konkuk-startup-external": {"patterns": [r"BoardView\.do"]}, "konkuk-startup-internal": {"patterns": [r"BoardView\.do"]},
    # ── 국민대 ──
    "kookmin-career-local": {"patterns": [r"/education/local/\d+"]},
    "kookmin-general": {"patterns": [r"/notice/\d+/\d+"]}, "kookmin-lecture": {"patterns": [r"/notice/\d+/\d+"]},
    # ── 숭실대 ──
    "ssu-general": {"patterns": [r"slug="]},
    "ssu-biz": {"patterns": [r"read\.do\?aId="]},
    # ── 공공 ──
    "seoul-youth-sprt": {"parser": "seoul_youth"}, "seoul-orang": {"parser": "seoul_youth"},
    "seoul-youth-notice": {"parser": "onclick_regex", "onclick": r"goView\('(\d+)'\)", "detail": "https://youth.seoul.go.kr/bbs/view.do?key=2303300002&pstSn={0}&sc_bbsCtgrySn=2304110001"},
    "kstartup-ongoing": {"parser": "onclick_regex", "onclick": r"go_view\((\d+)\)", "detail": "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?schM=view&pbancSn={0}"},
    "sba-ongoing": {"parser": "onclick_regex", "onclick": r"PostingDetail\.aspx\?p=1&(?:amp;)?mid=([0-9a-f-]+)", "detail": "https://www.sba.seoul.kr/Pages/BusinessApply/PostingDetail.aspx?p=1&mid={0}"},
    "campustown-programs": {"patterns": [r"/university_news/\d+"]}, "campustown-notice": {"patterns": [r"/sct_news/\d+"]},
    "sesac-offline": {"patterns": [r"courseDetail\.do\?crsSn=\d+"]},
    "job-alio-intern": {"patterns": [r"recruitview\.do\?idx=\d+"]},
    "dcamp-notice": {"patterns": [r"/news/notice/\d+"]},
    "startupall-events": {"patterns": [r"/programs/info/\d+"]},
    # ── 금융 ──
    "kofia-recruit": {"parser": "kofia"}, "shinhan-recruit": {"parser": "shinhan"},
    "kb-sec-recruit": {"patterns": [r"/ko/o/\d+"]},
    "mktest-notice": {"patterns": [r"view\.php\?id=mktest_notice&(?:amp;)?no=\d+"]},
    # ── 기술직 ──
    "work24-training": {"parser": "work24"},
    "sitedu-apply": {"parser": "sitedu"},
    "kofta-notice": {"parser": "onclick_regex", "onclick": r"fn_GoRead\('(\d+)'\)", "detail": "https://www.kofta.org/communication/board/Read.jsp?ntt_id={0}"},
    "youth-work-exp": {"parser": "onclick_regex", "onclick": r"fn_searchDetail\((\d+)\)", "detail": "https://yw.work24.go.kr/c/b/selectWkexBizList.do#biz-{0}"},
}
