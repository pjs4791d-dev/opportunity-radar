"""HTTP 수집 공통: User-Agent, 도메인별 최소 간격, robots.txt, 재시도.

명세서 5-5 크롤링 예절을 여기서 강제한다.
"""
import time, re, json, pathlib, urllib.robotparser, threading
from urllib.parse import urlsplit
import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))["collector"]

UA = CFG["user_agent"]
MIN_DELAY = float(CFG.get("min_delay_seconds", 2))
TIMEOUT = 25

_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
_last_hit = {}          # domain -> time.time()
_robots = {}            # domain -> RobotFileParser | None
_lock = threading.Lock()
_dom_locks = {}         # domain -> Lock (도메인별 직렬화)


def _domain(url):
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def _robots_ok(url):
    d = _domain(url)
    with _dlock(d):
        return _robots_ok_locked(url, d)


def _robots_ok_locked(url, d):
    if d not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = _session.get(d + "/robots.txt", timeout=10)
            if r.status_code == 200 and r.text.strip():
                rp.parse(r.text.splitlines())
                _robots[d] = rp
            else:
                _robots[d] = None
        except Exception:
            _robots[d] = None
    rp = _robots[d]
    if rp is None:
        return True
    return rp.can_fetch("*", url)


def _dlock(d):
    with _lock:
        if d not in _dom_locks:
            _dom_locks[d] = threading.Lock()
        return _dom_locks[d]


def _throttle(url):
    """같은 도메인은 한 번에 하나씩, 최소 MIN_DELAY 간격. 다른 도메인끼리는 병렬 허용."""
    d = _domain(url)
    with _dlock(d):
        wait = MIN_DELAY - (time.time() - _last_hit.get(d, 0))
        if wait > 0:
            time.sleep(wait)
        _last_hit[d] = time.time()


class Blocked(Exception):
    pass


def get(url, *, params=None, retries=2, json_body=False, encoding=None):
    """GET → (text 또는 json). robots.txt 금지 경로면 Blocked."""
    if not _robots_ok(url):
        raise Blocked(f"robots.txt 금지: {url}")
    last = None
    for attempt in range(retries + 1):
        _throttle(url)
        try:
            r = _session.get(url, params=params, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code >= 500:
                last = f"HTTP {r.status_code}"
                continue
            if r.status_code >= 400:
                raise requests.HTTPError(f"HTTP {r.status_code} {url}")
            if json_body:
                return r.json()
            if encoding:
                r.encoding = encoding
            elif not r.encoding or r.encoding.lower() in ("iso-8859-1", "ascii"):
                r.encoding = r.apparent_encoding
            return r.text
        except (requests.Timeout, requests.ConnectionError) as e:
            last = str(e)[:120]
            if "SSL" in last or "Max retries" in last:
                txt = _curl(url, params)
                if txt is not None:
                    return json.loads(txt) if json_body else txt
    raise RuntimeError(f"요청 실패({last}): {url}")


def _curl(url, params=None):
    """requests 가 TLS 문제로 실패할 때(로컬 LibreSSL 등) curl 로 한 번 더 시도."""
    import subprocess
    from urllib.parse import urlencode
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    try:
        r = subprocess.run(["curl", "-sL", "-m", str(TIMEOUT), "-A", UA, url], capture_output=True, timeout=TIMEOUT + 5)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
    except Exception:
        pass
    return None
