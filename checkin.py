import os
import json
import time
import random
import requests
from pypushdeer import PushDeer


CHECKIN_URL = "https://glados.cloud/api/user/checkin"
STATUS_URL = "https://glados.cloud/api/user/status"

HEADERS_BASE = {
    "origin": "https://glados.cloud",
    "referer": "https://glados.cloud/console/checkin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "content-type": "application/json;charset=UTF-8",
}

PAYLOAD = {"token": "glados.cloud"}
TIMEOUT = 10


def push(token: str, title: str, text: str):
    if not token:
        return
    url = 'http://www.pushplus.plus/send'
    content_body = text.replace("\n", "<br>")
    data = {
        "token": token,
        "title": title,
        "content": content_body,
        "template": "markdown",
    }
    try:
        resp = requests.post(
            url, 
            json=data, 
            headers={'content-type': 'application/json'}
        )
    except Exception as e:
        print(f"PushPlus 推送失败: {e}")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def main():
    sckey = os.getenv("SENDKEY", "")
    cookies_env = os.getenv("COOKIES", "")
    cookies = [c.strip() for c in cookies_env.split("&") if c.strip()]

    if not cookies:
        push(sckey, "GLaDOS 签到", "❌ 未检测到 COOKIES")
        return

    session = requests.Session()
    ok = fail = repeat = 0
    lines = []

    for idx, cookie in enumerate(cookies, 1):
        headers = dict(HEADERS_BASE)
        headers["cookie"] = cookie

        email = "unknown"
        points = "-"
        days = "-"
        total_points = " "
        
        try:
            r = session.post(
                CHECKIN_URL,
                headers=headers,
                data=json.dumps(PAYLOAD),
                timeout=TIMEOUT,
            )

            j = safe_json(r)
            print(f"--- 签到接口返回 (Raw Data) ---")
            print(json.dumps(j, indent=4, ensure_ascii=False))
            print("--------------------------------")
            msg = j.get("message", "")
            msg_lower = msg.lower()

            if "got" in msg_lower:
                ok += 1
                points = j.get("points", "-")
                status = "✅ 成功"
            elif "repeat" in msg_lower or "already" in msg_lower:
                repeat += 1
                status = "🔁 已签到"
            else:
                fail += 1
                status = "❌ 失败"
                
            try:
                checkin_list = j.get("list", [])
                if checkin_list and isinstance(checkin_list, list) and len(checkin_list) > 0:
                    balance_str = checkin_list[0].get("balance")
                    if balance_str:
                        total_points = int(float(balance_str))
            except Exception:
                pass
                
            # 状态接口（允许失败）
            s = session.get(STATUS_URL, headers=headers, timeout=TIMEOUT)
            sj = safe_json(s).get("data") or {}
            email = sj.get("email", email)
            if sj.get("leftDays") is not None:
                days = f"{int(float(sj['leftDays']))} 天"

        except Exception:
            fail += 1
            status = "❌ 异常"

        lines.append(f"{idx}. {email} | {status} | P:{points} | Total:{total_points} | 剩余:{days}")
        time.sleep(random.uniform(1, 2))
        
    if fail > 0:
        title = "GLaDOS ⚠️ 签到异常 - 请检查 Cookie"
    elif ok > 0:
        if len(cookies) == 1 and points != "-":
             title = f"GLaDOS ✅ 签到成功 (+{points} Point)"
        else:
             title = f"GLaDOS ✅ 成功签到 {ok} 个账号"
    elif repeat > 0:
        title = "GLaDOS 👋 今日已签 (无变化)"
    else:
        title = "GLaDOS 签到通知"
    content = "\n".join(lines)

    print(content)
    push(sckey, title, content)


if __name__ == "__main__":
    main()
