"""健康探针 & 自动恢复 — 所有检测和恢复函数"""
import json
import os
import sqlite3
import subprocess
import time
import urllib.request

from .config import (
    find_hermes_exe,
    DEFAULT_ADS_API,
    DEFAULT_ADS_PROFILE,
    DEFAULT_DB_PATH,
    CRON_JOBS,
)


# ─── 探针 ───────────────────────────────────────────

def check_hermes_process():
    """Hermes 桌面端是否在运行"""
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq hermes*", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        if "hermes" in r.stdout.lower():
            return True, "运行中"
        return False, "未找到Hermes进程"
    except Exception as e:
        return False, str(e)


def check_browser(ads_api=None, ads_profile=None):
    """AdsPower 浏览器 WebSocket 是否可达"""
    ads_api = ads_api or DEFAULT_ADS_API
    ads_profile = ads_profile or DEFAULT_ADS_PROFILE

    if not ads_profile:
        return True, "未配置ADS_PROFILE，跳过浏览器检测"

    try:
        url = f"{ads_api}/api/v1/browser/active?user_id={ads_profile}"
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        if data.get("code") == 0 and data.get("data", {}).get("status") == "Active":
            return True, "浏览器活跃"
        return False, f"浏览器状态: {data.get('data', {}).get('status', '未知')}"
    except Exception as e:
        return False, f"连接失败: {e}"


def check_disk():
    """C 盘剩余空间（Windows）"""
    try:
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p("C:\\"), None, None, ctypes.pointer(free_bytes))
        free_gb = free_bytes.value / 1024 ** 3
        total = 40  # 总容量假设（可改为实际获取）
        pct = free_gb / total * 100
        return pct > 10, f"剩余 {free_gb:.1f}GB / {total}GB ({pct:.0f}%)"
    except Exception:
        return True, "无法检测磁盘"


def check_database(db_path=None):
    """数据库是否可读写"""
    db_path = db_path or DEFAULT_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        return True, "正常"
    except Exception as e:
        return False, str(e)


def check_internet():
    """通用网络连通性"""
    targets = [
        "https://www.baidu.com",
        "https://www.google.com",
        "https://seller-my.tiktok.com",
    ]
    for url in targets:
        try:
            r = urllib.request.urlopen(url, timeout=8)
            return True, f"可达 ({url} -> {r.getcode()})"
        except Exception:
            continue
    return False, "所有出口均不可达"


def check_cron_jobs(hermes_exe=None):
    """检查 cron 任务是否完整"""
    hermes_exe = hermes_exe or find_hermes_exe()
    if not hermes_exe or not os.path.isfile(hermes_exe):
        return False, "未找到Hermes可执行文件"

    try:
        r = subprocess.run(
            [hermes_exe, "cron", "list"],
            capture_output=True, text=True, timeout=15,
        )
        output = r.stdout
        issues = []
        for name in CRON_JOBS:
            if name not in output:
                issues.append(f"{name}: 缺失")
        if issues:
            return False, "; ".join(issues)
        return True, f"全部{len(CRON_JOBS)}个任务正常"
    except Exception as e:
        return False, str(e)


def get_ip():
    """获取本机公网 IP"""
    try:
        r = urllib.request.urlopen("https://myip.ipip.net", timeout=8)
        return r.read().decode().strip()
    except Exception:
        return "获取失败"


# ─── 自动恢复 ───────────────────────────────────────

def recover_hermes():
    """尝试启动 Hermes"""
    hermes_exe = find_hermes_exe()
    if not hermes_exe:
        return False, "未找到Hermes可执行文件"
    try:
        subprocess.Popen([hermes_exe], shell=True)
        time.sleep(5)
        ok, msg = check_hermes_process()
        return ok, msg
    except Exception as e:
        return False, str(e)


def recover_browser(ads_api=None, ads_profile=None):
    """尝试重启 AdsPower 浏览器"""
    ads_api = ads_api or DEFAULT_ADS_API
    ads_profile = ads_profile or DEFAULT_ADS_PROFILE

    if not ads_profile:
        return False, "未配置ADS_PROFILE"

    try:
        url = f"{ads_api}/api/v1/browser/start?user_id={ads_profile}&open_tabs=1"
        r = urllib.request.urlopen(url, timeout=15)
        data = json.loads(r.read())
        if data.get("code") == 0:
            time.sleep(8)
            ok, msg = check_browser(ads_api, ads_profile)
            return ok, msg
        return False, f"API返回: {data}"
    except Exception as e:
        return False, str(e)
