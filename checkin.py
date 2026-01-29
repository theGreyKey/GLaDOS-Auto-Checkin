import os
import json
import time
import random
import requests
import sys

# ================= 配置区 =================
# 多域名支持，防屏蔽
DOMAINS = [
    "https://glados.cloud",
    "https://glados.rocks",
    "https://glados.network",
]

HEADERS_BASE = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "content-type": "application/json;charset=UTF-8",
}

# ================= 工具函数 =================

def push_plus(token, title, content):
    """
    使用 PushPlus 推送 HTML 格式消息
    """
    if not token:
        return
    
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html",  # 注意这里改成了 html
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        print(f"PushPlus 响应: {resp.text}")
    except Exception as e:
        print(f"PushPlus 推送失败: {e}")

def request_with_retry(session, method, path, headers, data=None):
    """
    自动在多个域名之间切换请求
    """
    for domain in DOMAINS:
        url = f"{domain}{path}"
        # 动态修改 Origin 和 Referer
        current_headers = headers.copy()
        current_headers['origin'] = domain
        current_headers['referer'] = f"{domain}/console/checkin"
        
        try:
            if method == 'POST':
                r = session.post(url, headers=current_headers, data=data, timeout=10)
            else:
                r = session.get(url, headers=current_headers, timeout=10)
            
            if r.status_code == 200:
                return r  # 请求成功直接返回
        except Exception as e:
            print(f"⚠️ 域名 {domain} 请求失败: {e}，尝试下一个...")
            continue
            
    return None # 所有域名都失败

def analyze_exchange(points, plans):
    """
    计算积分兑换情况
    """
    try:
        current_pts = int(float(points))
        lines = []
        # 遍历官方的兑换计划
        for plan in plans:
            cost = int(float(plan.get('points', 0)))
            days = plan.get('days', 0)
            if cost == 0: continue
            
            if current_pts >= cost:
                lines.append(f"<span style='color:#27ae60'>✅ {cost}分换{days}天 (可兑换)</span>")
            else:
                diff = cost - current_pts
                lines.append(f"<span style='color:#e74c3c'>❌ {cost}分换{days}天 (差{diff}分)</span>")
        return "<br>".join(lines)
    except:
        return "无法分析兑换数据"

def clean_cookie(raw_cookie):
    """
    简单的 Cookie 清洗，确保只保留关键部分
    """
    # 这里可以根据需要加强，目前保持简单
    return raw_cookie.strip()

# ================= 主逻辑 =================

def main():
    sckey = os.getenv("SENDKEY", "")
    cookies_env = os.getenv("COOKIES", "")
    cookies = [clean_cookie(c) for c in cookies_env.split("&") if c.strip()]

    if not cookies:
        print("❌ 未检测到 COOKIES")
        return

    session = requests.Session()
    
    # 统计数据
    stats = {'ok': 0, 'fail': 0, 'repeat': 0, 'code_fail': False}
    html_cards = [] # 存放每个账号的 HTML 卡片
    
    for idx, cookie in enumerate(cookies, 1):
        headers = dict(HEADERS_BASE)
        headers["cookie"] = cookie
        
        print(f"\n====== 处理账号 {idx} ======")
        
        # 初始化变量
        email = "Unknown"
        status_text = "❌ 未知错误"
        points_total = 0
        points_delta = 0
        left_days = 0
        exchange_html = "暂无数据"
        
        try:
            # --- 1. 签到 (带域名重试) ---
            r = request_with_retry(session, 'POST', '/api/user/checkin', headers, json.dumps({"token": "glados.cloud"}))
            
            checkin_msg = "网络请求失败"
            if r:
                j = r.json()
                checkin_msg = j.get("message", "")
                code = j.get("code", -999)
                
                # 记录状态
                if code == 0:
                    stats['ok'] += 1
                    status_text = "✅ 签到成功"
                    points_delta = int(float(j.get("points", 0)))
                elif code == 1:
                    stats['repeat'] += 1
                    status_text = "🔁 今日已签"
                elif code == -2:
                    stats['code_fail'] = True
                    status_text = "🚨 Cookie失效"
                else:
                    stats['fail'] += 1
                    status_text = f"❌ 失败({code})"
            else:
                stats['fail'] += 1

            # --- 2. 获取状态与积分详情 (带域名重试) ---
            # 即使签到失败，也尝试获取一下状态，万一是重复签到呢
            r_status = request_with_retry(session, 'GET', '/api/user/status', headers)
            if r_status:
                d = r_status.json().get('data', {})
                email = d.get('email', 'Unknown')
                left_days = int(float(d.get('leftDays', 0)))
            
            # --- 3. 获取积分历史与兑换计划 (新增功能) ---
            r_points = request_with_retry(session, 'GET', '/api/user/points', headers)
            if r_points:
                p_data = r_points.json()
                points_total = int(float(p_data.get('points', 0)))
                # 分析兑换
                exchange_html = analyze_exchange(points_total, p_data.get('plans', []).values())

        except Exception as e:
            print(f"账号处理异常: {e}")
            status_text = "❌ 脚本异常"
            stats['fail'] += 1

        # --- 生成单个账号的 HTML 卡片 ---
        # 样式参考了你提供的参考代码，做了一些简化和美化
        card = f"""
        <div style="border:1px solid #ddd; border-radius:8px; padding:15px; margin-bottom:15px; background-color:#fff; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
            <div style="border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:10px; font-weight:bold; font-size:16px; color:#333;">
                👤 账号 {idx}: {email}
            </div>
            <div style="font-size:14px; line-height:1.6; color:#555;">
                <p><b>📅 状态:</b> {status_text}</p>
                <p><b>💰 积分:</b> <span style="color:#d35400; font-weight:bold">{points_total}</span> 
                   <span style="color:#27ae60; font-size:12px">(本轮 {points_delta:+})</span>
                </p>
                <p><b>⏳ 剩余:</b> {left_days} 天</p>
            </div>
            <div style="margin-top:10px; padding:10px; background-color:#f9f9f9; border-radius:5px; font-size:13px;">
                <b>🎁 兑换建议:</b><br>
                {exchange_html}
            </div>
        </div>
        """
        html_cards.append(card)
        
        # 控制台打印简单日志
        print(f"  > 结果: {status_text} | 剩余: {left_days}天 | 总分: {points_total}")
        time.sleep(random.uniform(1, 3))

    # ================= 汇总与推送 =================
    
    # 生成标题
    if stats['code_fail']:
        title = "GLaDOS 🚨 Cookie 已失效 - 请检查"
    elif stats['fail'] > 0:
        title = f"GLaDOS ⚠️ 完成 (成功{stats['ok']}/失败{stats['fail']})"
    else:
        title = f"GLaDOS ✅ 全部完成 (成功{stats['ok']}/重复{stats['repeat']})"

    # 组合最终 HTML
    final_content = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <h2 style="text-align:center; color:#2c3e50;">GLaDOS 签到报告</h2>
        <p style="text-align:center; color:#7f8c8d; font-size:12px;">{time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        {''.join(html_cards)}
    </div>
    """
    
    print("\n====== 推送内容预览 ======")
    # print(final_content) # 调试时可以取消注释
    
    push_plus(sckey, title, final_content)

if __name__ == "__main__":
    main()
