"""
抖音创作者视频数据抓取脚本 v2
使用更完整的请求参数和 headers
"""
import argparse
import json
import os
import sys
import time
import re
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("ERROR: requests 库未安装，请运行: pip install requests", file=sys.stderr)
    sys.exit(1)


def extract_ms_token(cookie_str):
    """从 cookie 中提取 msToken"""
    match = re.search(r'msToken=([^;]+)', cookie_str)
    return match.group(1) if match else ""


def fetch_videos(sec_user_id, cookie_str, days):
    """抓取指定用户的视频列表"""
    ms_token = extract_ms_token(cookie_str)
    if not ms_token:
        ms_token = "placeholder_token"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
        "Referer": f"https://www.douyin.com/user/{sec_user_id}",
        "Cookie": cookie_str,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    # 尝试使用 /aweme/v1/web/aweme/post/ 端点
    url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
    
    cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    all_videos = []
    max_cursor = 0
    
    while True:
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "sec_user_id": sec_user_id,
            "max_cursor": str(max_cursor),
            "locate_query": "false",
            "show_live_replay_strategy": "1",
            "need_time_list": "1",
            "time_list_query": "0",
            "whale_cut_token": "",
            "cut_version": "1",
            "count": "18",
            "publish_video_strategy_type": "2",
            "update_version_code": "170400",
            "platform": "PC",
            "downlink": "10",
            "pc_client_type": "1",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "1707",
            "screen_height": "960",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Edge",
            "browser_version": "148.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "148.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "16",
            "device_memory": "16",
            "resolution": "1707*960",
            "msToken": ms_token,
            "verifyFp": "verify_mph3bvzk_vLngvoLD_KZ0d_4sqq_AhpQ_QpxwLDxaHPax",
            "fp": "verify_mph3bvzk_vLngvoLD_KZ0d_4sqq_AhpQ_QpxwLDxaHPax",
        }
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            data = resp.json()
        except Exception as e:
            print(json.dumps({"error": f"请求失败: {str(e)}"}, ensure_ascii=False))
            sys.exit(1)
        
        status_code = data.get("status_code", -1)
        if status_code == 5:
            # 可能需要 a_bogus 签名，尝试备用方案
            print(json.dumps({
                "error": "status_code=5: 抖音 API 需要反爬签名(a_bogus/X-Bogus)，当前无法自动生成。",
                "suggestion": "请在浏览器中手动访问用户主页，使用开发者工具(F12)->Network 查看实际请求参数中的 a_bogus 值",
                "log_pb": data.get("log_pb", {})
            }, ensure_ascii=False))
            sys.exit(1)
        
        if status_code != 0:
            print(json.dumps({"error": f"API 返回错误, status_code={status_code}", "raw": data}, ensure_ascii=False))
            sys.exit(1)
        
        aweme_list = data.get("aweme_list") or []
        if not aweme_list:
            break
        
        stop = False
        for item in aweme_list:
            create_time = item.get("create_time", 0)
            if create_time < cutoff_time:
                stop = True
                continue
            video_info = _parse_video(item)
            if video_info:
                all_videos.append(video_info)
        
        if stop:
            break
        
        has_more = data.get("has_more", 0)
        max_cursor = data.get("max_cursor", 0)
        
        if not has_more:
            break
        
        time.sleep(1)
    
    return _output(all_videos)


def _parse_video(item):
    """解析单条视频数据"""
    stats = item.get("statistics", {})
    return {
        "title": item.get("desc", ""),
        "create_time": item.get("create_time", 0),
        "create_time_str": datetime.fromtimestamp(item.get("create_time", 0)).strftime("%Y-%m-%d %H:%M"),
        "likes": stats.get("digg_count", 0),
        "comments": stats.get("comment_count", 0),
        "shares": stats.get("share_count", 0),
        "plays": stats.get("play_count", 0),
        "video_id": item.get("aweme_id", ""),
    }


def _output(videos):
    """输出结果"""
    print(json.dumps({"total": len(videos), "videos": videos}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抖音视频数据抓取")
    parser.add_argument("--sec_user_id", required=True, help="用户 sec_user_id")
    parser.add_argument("--cookie_file", required=True, help="Cookie 文件路径")
    parser.add_argument("--days", type=int, default=7, help="抓取最近 N 天的视频")
    args = parser.parse_args()
    
    if not os.path.exists(args.cookie_file):
        print(f"ERROR: Cookie 文件不存在: {args.cookie_file}", file=sys.stderr)
        sys.exit(1)
    
    with open(args.cookie_file, "r", encoding="utf-8") as f:
        cookie_str = f.read().strip()
    
    fetch_videos(args.sec_user_id, cookie_str, args.days)
