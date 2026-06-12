"""配置加载 — 自动检测 Hermes 版本，消除硬编码"""
import os
import sys


def get_home():
    """用户主目录"""
    return os.path.expanduser("~")


def get_scripts_dir():
    """Hermes 脚本目录"""
    return os.path.join(get_home(), ".hermes", "scripts")


def find_hermes_exe():
    """自动查找最新版本的 Hermes 可执行文件"""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return None

    versions_dir = os.path.join(appdata, "cn.org.hermesagent.desktop", "runtime", "versions")
    if not os.path.isdir(versions_dir):
        return None

    candidates = sorted(os.listdir(versions_dir), reverse=True)
    for ver in candidates:
        exe = os.path.join(versions_dir, ver, "hermes-agent-cn-runtime-win32-x64.exe")
        if os.path.isfile(exe):
            return exe
    return None


def get_hermes_home():
    """Hermes 内部脚本目录"""
    appdata = os.environ.get("APPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Roaming"))
    return os.path.join(appdata, "cn.org.hermesagent.desktop", "runtime", "hermes-home", "scripts")


def load_webhook():
    """加载飞书 Webhook 地址"""
    scripts_dir = get_scripts_dir()
    webhook_path = os.path.join(scripts_dir, ".report_webhook")
    if os.path.isfile(webhook_path):
        with open(webhook_path) as f:
            hook = f.read().strip()
            if hook:
                return hook
    return None


# 常量默认值
DEFAULT_ADS_API = "http://local.adspower.net:50325"
DEFAULT_ADS_PROFILE = os.environ.get("ADS_PROFILE", "")
DEFAULT_DB_PATH = os.path.join(get_home(), ".tkads", "data", "analytics.db")

# Cron 任务定义（供检查和报告使用）
CRON_JOBS = {
    "daily-collect":        {"schedule": "0 7 * * *"},
    "daily-github-backup":  {"schedule": "0 11 * * *"},
    "daily-ad-report":      {"schedule": "0 9 * * *"},
    "daily-creator-report": {"schedule": "0 9 * * *"},
    "cron-guardian":        {"schedule": "every 120m"},
}
