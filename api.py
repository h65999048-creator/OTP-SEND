# Dependencies: pip install flask requests urllib3 curl_cffi

import random
import urllib3
from curl_cffi import requests as cffi_requests
from flask import Flask, request, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


def insert_dot(email: str) -> str:
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    if len(local) < 2:
        return email
    pos = random.randint(1, len(local) - 1)
    return f"{local[:pos]}.{local[pos:]}@{domain}"


def send_otp(email: str) -> dict:
    target = insert_dot(email)
    url = "https://100067.connect.garena.com/game/account_security/swap:send_otp"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.41(TECNO KJ5 ;Android 13;en;HK;app 1.123.1 2019120270;)",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }
    data = {"app_id": "100067", "email": target, "locale": "hi_IN"}
    resp = cffi_requests.post(
        url,
        headers=headers,
        data=data,
        timeout=15,
        impersonate="chrome",
    )
    try:
        j = resp.json()
    except Exception:
        j = {}
    return {"sent_to": target, "response": j}


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
        return jsonify({"ok": False, "error": "network_error", "detail": str(e)}), 502

    j = result["response"]
    err = j.get("error")
    code = j.get("code")
    res = j.get("result")

    if res == 0:
        status, ok = "success", True
    elif err == "error_too_many_requests" or code == 1006:
        status, ok = "rate_limited", False
    elif err == "error_no_binding_found":
        status, ok = "not_bound", False
    elif err == "error_params":
        status, ok = "invalid_email", False
    else:
        status, ok = "unknown", False

    return jsonify({
        "ok": ok,
        "status": status,
        "sent_to": result["sent_to"],
        "raw": j,
    }), (200 if ok else 429)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
