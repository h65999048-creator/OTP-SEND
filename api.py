# Dependencies: pip install flask requests urllib3 gunicorn

import random
import time
import threading
import requests
import urllib3
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# =========================================================
# PROXY POOL  — apne real proxies yahan daalo
# Format: scheme://host:port   (http://1.2.3.4:8080)
# =========================================================

PROXY_POOL: List[str] = [
    "http://142.93.202.130:3128",
    "http://20.219.180.167:8080",
    "http://103.152.112.145:80",
    "http://194.233.69.89:443",
    "http://45.77.148.235:8080",
    "http://157.230.113.196:80",
    "http://51.79.50.75:8080",
    "http://159.89.83.187:80",
    "http://167.99.120.35:8080",
    "http://64.225.4.98:3128",
    "http://134.209.29.44:80",
    "http://165.227.211.41:3128",
    "http://143.198.65.12:80",
    "http://64.227.12.150:8080",
    "http://178.128.20.100:80",
    "http://159.203.61.44:3128",
    "http://68.183.21.209:80",
    "http://206.189.130.10:8080",
    "http://167.172.22.88:3128",
    "http://104.248.50.30:80",
]

PROXY_BLACKLIST: set = set()
PROXY_LOCK = threading.Lock()
PROXY_HEALTH: Dict[str, float] = {}


def _fresh_proxies() -> List[str]:
    with PROXY_LOCK:
        alive = [p for p in PROXY_POOL if p not in PROXY_BLACKLIST]
    random.shuffle(alive)
    return alive


def _mark_dead(proxy: str) -> None:
    with PROXY_LOCK:
        PROXY_BLACKLIST.add(proxy)
        PROXY_HEALTH[proxy] = time.time()


def _proxy_dict(proxy: str) -> Dict[str, str]:
    return {"http": proxy, "https": proxy}


URL = "https://100067.connect.garena.com/game/account_security/swap:send_otp"

HEADERS: Dict[str, str] = {
    "User-Agent": "GarenaMSDK/4.0.41(TECNO KJ5 ;Android 13;en;HK;app 1.123.1 2019120270;)",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}

MAX_PROXY_TRIES = 6
TIMEOUT = 12


def insert_dot(email: str) -> str:
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    if len(local) < 2:
        return email
    pos = random.randint(1, len(local) - 1)
    return f"{local[:pos]}.{local[pos:]}@{domain}"


def _raw_post(payload: Dict[str, str], proxy: Optional[str]) -> requests.Response:
    kwargs: Dict[str, Any] = {
        "headers": HEADERS,
        "data": payload,
        "timeout": TIMEOUT,
        "verify": False,
    }
    if proxy:
        kwargs["proxies"] = _proxy_dict(proxy)
    return requests.post(URL, **kwargs)


def send_otp(email: str) -> Dict[str, Any]:
    target = insert_dot(email)
    payload = {"app_id": "100067", "email": target, "locale": "hi_IN"}
    tried: List[str] = []
    last_exc: Optional[Exception] = None

    for proxy in _fresh_proxies()[:MAX_PROXY_TRIES]:
        tried.append(proxy)
        try:
            resp = _raw_post(payload, proxy)
            try:
                j = resp.json()
            except Exception:
                j = {"_raw": resp.text[:200]}
            return {"sent_to": target, "response": j, "via": proxy, "tried": tried}
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError) as e:
            last_exc = e
            _mark_dead(proxy)
            time.sleep(0.1)
            continue
        except Exception as e:
            last_exc = e
            break

    try:
        resp = _raw_post(payload, None)
        try:
            j = resp.json()
        except Exception:
            j = {"_raw": resp.text[:200]}
        return {"sent_to": target, "response": j, "via": "direct", "tried": tried}
    except Exception as e:
        return {
            "sent_to": target,
            "response": {"error": "all_proxies_failed", "detail": str(last_exc or e)},
            "via": "none",
            "tried": tried,
        }


def classify(j: Dict[str, Any]) -> str:
    err = j.get("error")
    code = j.get("code")
    res = j.get("result")
    if res == 0:
        return "success"
    if err == "error_too_many_requests" or code == 1006:
        return "rate_limited"
    if err == "error_no_binding_found":
        return "not_bound"
    if err == "error_params":
        return "invalid_email"
    if err == "all_proxies_failed":
        return "network_error"
    return "unknown"


@app.route("/api", methods=["GET", "POST"])
def api():
    if request.method == "GET":
        email = request.args.get("email", "").strip()
    else:
        body = request.get_json(silent=True) or {}
        email = str(body.get("email", "")).strip() or request.form.get("email", "").strip()

    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "invalid_email"}), 400

    try:
        result = send_otp(email)
    except Exception as e:
        return jsonify({"ok": False, "error": "fatal", "detail": str(e)}), 500

    j = result["response"]
    status = classify(j)
    ok = status == "success"

    http_code = 200 if ok else (429 if status == "rate_limited" else 400 if status == "invalid_email" else 502)

    return jsonify({
        "ok": ok,
        "status": status,
        "sent_to": result["sent_to"],
        "via": result.get("via"),
        "tried": result.get("tried", []),
        "raw": j,
    }), http_code


@app.route("/health", methods=["GET"])
def health():
    with PROXY_LOCK:
        alive = len([p for p in PROXY_POOL if p not in PROXY_BLACKLIST])
    return jsonify({
        "ok": True,
        "proxies_total": len(PROXY_POOL),
        "proxies_alive": alive,
        "proxies_dead": len(PROXY_BLACKLIST),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)