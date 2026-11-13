# Pehle dependencies install karo: pip install curl_cffi
from curl_cffi import requests as cffi_requests

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
    
    # Key change yahan hai: impersonate parameter add karo
    resp = cffi_requests.post(
        url, 
        headers=headers, 
        data=data, 
        timeout=15,
        impersonate="chrome"  # Chrome ka TLS/JA3 fingerprint use karega
    )
    try:
        j = resp.json()
    except Exception:
        j = {}
    return {"sent_to": target, "response": j}
