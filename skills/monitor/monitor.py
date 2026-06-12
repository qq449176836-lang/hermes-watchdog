#!/usr/bin/env python3
"""
Monitor — 全能守护者核心引擎
分级告警 + 探针检测 + 自动恢复 + 去重通知

用法:
    python monitor.py            # 完整模式
    python monitor.py --fast     # 快速模式（仅关键探针）
"""
import sys
import os
from datetime import datetime

# 确保项目根目录在 sys.path 中，以便导入 shared
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from shared.config import (
    find_hermes_exe,
    get_scripts_dir,
    load_webhook,
    DEFAULT_ADS_API,
    DEFAULT_ADS_PROFILE,
    CRON_JOBS,
)
from shared.state import load_state, save_state, log_event
from shared.feishu import notify
from shared.checks import (
    check_hermes_process,
    check_browser,
    check_disk,
    check_database,
    check_internet,
    check_cron_jobs,
    get_ip,
    recover_hermes,
    recover_browser,
)

# ─── 告警汇总 & 去重 ─────────────────────────────────

def run(fast_mode=False):
    state = load_state()
    now = datetime.now()
    changed = False
    webhook = load_webhook()
    hermes_exe = find_hermes_exe()

    p0_alerts = []
    p1_alerts = []
    p2_alerts = []

    # ── 1. Hermes 进程 ──
    hermes_ok, hermes_msg = check_hermes_process()
    prev = state["checks"].get("hermes", "unknown")
    new_status = "up" if hermes_ok else "down"
    if prev != new_status:
        state["checks"]["hermes"] = new_status
        changed = True
        if not hermes_ok:
            p0_alerts.append(("Hermes进程", hermes_msg))
            log_event("P0", "hermes", hermes_msg)
            recovered, rmsg = recover_hermes()
            if recovered:
                state["checks"]["hermes"] = "up"
                state["recovery_count"] = state.get("recovery_count", 0) + 1
                log_event("INFO", "hermes", f"自动恢复成功: {rmsg}", recovered=True)

    # ── 2. 浏览器 ──
    browser_ok, browser_msg = check_browser(DEFAULT_ADS_API, DEFAULT_ADS_PROFILE)
    prev = state["checks"].get("browser", "unknown")
    new_status = "up" if browser_ok else "down"
    if prev != new_status:
        state["checks"]["browser"] = new_status
        changed = True
        if not browser_ok:
            p1_alerts.append(("AdsPower浏览器", browser_msg))
            log_event("P1", "browser", browser_msg)
            recovered, rmsg = recover_browser(DEFAULT_ADS_API, DEFAULT_ADS_PROFILE)
            if recovered:
                state["checks"]["browser"] = "up"
                state["recovery_count"] = state.get("recovery_count", 0) + 1
                log_event("INFO", "browser", f"自动恢复成功: {rmsg}", recovered=True)

    # ── 3. 磁盘（非 fast） ──
    if not fast_mode:
        disk_ok, disk_msg = check_disk()
        prev = state["checks"].get("disk", "unknown")
        new_status = "ok" if disk_ok else "low"
        if prev != new_status:
            state["checks"]["disk"] = new_status
            changed = True
            if not disk_ok:
                p2_alerts.append(("磁盘空间", disk_msg))
                log_event("P2", "disk", disk_msg)

    # ── 4. 数据库 ──
    db_ok, db_msg = check_database()
    prev = state["checks"].get("database", "unknown")
    new_status = "up" if db_ok else "down"
    if prev != new_status:
        state["checks"]["database"] = new_status
        changed = True
        if not db_ok:
            p1_alerts.append(("数据库", db_msg))
            log_event("P1", "database", db_msg)

    # ── 5. 网络 ──
    net_ok, net_msg = check_internet()
    prev = state["checks"].get("internet", "unknown")
    new_status = "up" if net_ok else "down"
    if prev != new_status:
        state["checks"]["internet"] = new_status
        changed = True
        if not net_ok:
            p2_alerts.append(("TikTok网络", net_msg))
            log_event("P2", "internet", net_msg)

    # ── 6. Cron 任务（非 fast） ──
    if not fast_mode:
        cron_ok, cron_msg = check_cron_jobs(hermes_exe)
        prev = state["checks"].get("cron", "unknown")
        new_status = "up" if cron_ok else "down"
        if prev != new_status:
            state["checks"]["cron"] = new_status
            changed = True
            if not cron_ok:
                p1_alerts.append(("Cron任务", cron_msg))
                log_event("P1", "cron", cron_msg)

    # ── 7. 自动恢复统计 ──
    rc = state.get("recovery_count", 0)
    if rc > 0:
        p2_alerts.append(("自动恢复", f"本周期已自动恢复 {rc} 次"))

    # ─── 发送通知（仅状态变化时）───
    if changed:
        for name, msg in p0_alerts:
            is_down = "未找到" in msg
            title = f"{'🔥' if is_down else '✅'} {name}"
            body = f"{'❌ 进程挂了' if is_down else '✅ 已恢复'}\n详情: {msg}"
            notify(webhook, "P0", title, body)

        for name, msg in p1_alerts:
            is_down = any(k in msg for k in ("失败", "Error", "缺失"))
            title = f"{'⚠️' if is_down else '✅'} {name}"
            body = f"{'异常' if is_down else '已恢复'}\n{msg}"
            notify(webhook, "P1", title, body)

        if p2_alerts:
            lines = []
            for n, m in p2_alerts:
                is_bad = any(k in m for k in ("失败", "低"))
                lines.append(f"{'❌' if is_bad else 'ℹ️'} {n}: {m}")
            notify(webhook, "P2", "系统状态变化", "\n".join(lines))

    # ─── 定时报告（完整模式）───
    if not fast_mode:
        ip = get_ip()
        STATUS_EMOJI = {"up": "✅", "down": "❌", "ok": "✅", "low": "⚠️", "unknown": "❓"}
        LABELS = {
            "hermes": "Hermes进程", "browser": "浏览器", "disk": "磁盘空间",
            "database": "数据库", "internet": "网络", "cron": "定时任务",
        }

        summary = [
            "🤖 **全能守护者健康报告**",
            f"🕐 {now.strftime('%Y-%m-%d %H:%M')}",
            "",
            f"🌐 **公网IP**: {ip}",
            "",
        ]
        for k, v in state["checks"].items():
            emoji = STATUS_EMOJI.get(v, "❓")
            label = LABELS.get(k, k)
            summary.append(f"{emoji} **{label}**: {v}")
        summary.append("")
        summary.append(f"🤖 自动恢复: {rc} 次" if rc > 0 else "🤖 自动恢复: 无异常")
        summary.append("")
        summary.append("📋 任务时间表")
        summary.append("07:00 数据采集 | 09:00 两份日报 | 11:00 GitHub备份")
        summary.append("⏱ 探针每30分钟 | 🩺 完整体检每2小时")

        notify(webhook, "P2", "系统健康报告", "\n".join(summary))

    save_state(state)
    return 0 if hermes_ok else 1


if __name__ == "__main__":
    fast = "--fast" in sys.argv
    sys.exit(run(fast_mode=fast))
