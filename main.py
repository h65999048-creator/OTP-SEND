# Dependencies: pip install requests urllib3

import os
import sys
import random
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

C = "\033[1;36m"
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
W = "\033[1;37m"
S = "\033[0m"


def clear() -> None:
    os.system('clear' if os.name == 'posix' else 'cls')


def draw_line() -> None:
    print(f"{C}{'═' * 60}{S}")


def banner() -> None:
    clear()
    print(f"""{C}
         ███████╗███████╗      ███████╗███╗   ███╗ █████╗ ██╗██╗
         ██╔════╝██╔════╝      ██╔════╝████╗ ████║██╔══██╗██║██║
         █████╗  █████╗        █████╗  ██╔████╔██║███████║██║██║
         ██╔══╝  ██╔══╝        ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║
         ██║     ███████╗      ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗
         ╚═╝     ╚══════╝      ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝{S}""")
    print(f"{C}{'═' * 17} FF EMAIL DOT-OTP SENDER {'═' * 17}{S}")
    print()
    print(f" {C}⊙ {W}DEVELOPER : {C}@Flash_0710{S}")
    print(f" {C}⊙ {W}MODE      : {G}SINGLE DOT-INSERT OTP{S}")
    print()
    draw_line()


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
    resp = requests.post(url, headers=headers, data=data, timeout=15)
    try:
        j = resp.json()
    except Exception:
        j = {}
    return {"sent_to": target, "response": j}


def main() -> None:
    while True:
        banner()
        print()
        email = input(f"{Y} [>] {W}Enter Email: {S}").strip()

        if not email or "@" not in email:
            print(f"\n{R} [!] Invalid / empty email.{S}\n")
            input(f"{C} [➔] Press [ENTER] to try again...{S}")
            continue

        print()
        try:
            result = send_otp(email)
            j = result["response"]
            err = j.get("error")
            code = j.get("code")
            res = j.get("result")

            if res == 0:
                print(f"{G} [✓] OTP SENT → {result['sent_to']}{S}")
            elif err == "error_too_many_requests" or code == 1006:
                print(f"{R} [✗] Rate limited on {result['sent_to']}{S}")
            elif err == "error_no_binding_found":
                print(f"{Y} [!] Email not bound to any account.{S}")
            elif err == "error_params":
                print(f"{R} [✗] Invalid / Wrong email.{S}")
            else:
                print(f"{Y} [!] Response: {j}{S}")
        except Exception as e:
            print(f"{R} [✗] Network error: {e}{S}")

        draw_line()
        print()
        input(f"{C} [➔] Press [ENTER] to continue...{S}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{R} [!] Interrupted by user.{S}")
        sys.exit()