# 🐕 Hermes Watchdog

> Hermes Agent 全能守护者 — 一键部署的监控告警与自动恢复系统

[![GitHub](https://img.shields.io/badge/GitHub-hermes--watchdog-blue)](https://github.com/qq449176836-lang/hermes-watchdog)

## 概述

Hermes Watchdog 是一套即插即用的健康监控系统，专为 Hermes Agent 桌面端设计。
**Python 引擎**（主力）+ **Bash 脚本**（轻量补充）两条监控线，覆盖进程、浏览器、磁盘、网络、数据库等关键维度。

## 快速安装

```bash
# 方式1：一键部署（推荐）
git clone https://github.com/qq449176836-lang/hermes-watchdog.git
cd hermes-watchdog/skills/monitor
node deploy.cjs

# 方式2：手动部署
# 将 skills/monitor/ 复制到 ~/.hermes/scripts/
# 配置飞书 Webhook → 执行 node deploy.cjs
```

## 仓库结构

```
hermes-watchdog/
├── README.md                          # 本文件
├── config/
│   └── webhook.example                # 飞书 Webhook 配置模板
├── scripts/                           # Bash 监控脚本
│   ├── full-check.sh                  # 全面健康检查
│   └── health-monitor.sh              # 轻量健康检查
├── shared/                            # Python 共享库
│   ├── __init__.py
│   ├── checks.py                      # 探针检测 + 自动恢复
│   ├── config.py                      # 环境配置加载
│   ├── feishu.py                      # 飞书通知推送
│   └── state.py                       # 状态持久化 + 日志
└── skills/monitor/                    # 可部署监控技能
    ├── README.md
    ├── deploy.cjs                     # 一键部署脚本
    └── monitor.py                     # 监控核心引擎（v2）
```

## 监控维度

| 维度 | 级别 | 告警 | 自动恢复 |
|------|------|------|---------|
| 🔴 **Hermes 进程** | P0 | 飞书 @all | ✅ 自动重启 |
| 🟠 **AdsPower 浏览器** | P1 | 飞书通知 | ✅ 自动恢复 |
| 🟠 **数据库** | P1 | 飞书通知 | ❌ |
| 🟠 **Cron 任务** | P1 | 飞书通知 | ❌ |
| 🟡 **磁盘空间** | P2 | 汇总通知 | ❌ |
| 🟡 **网络连通性** | P2 | 汇总通知 | ❌ |

## 双循环运行

```
⏱ 快速探针（每30分钟）→ monitor --fast: 
   仅检查 Hermes 进程 + 浏览器，状态变化时通知

🩺 完整体检（每2小时） → monitor（完整模式）:
   所有维度 + 健康报告 + 公网 IP
```

## 飞书通知示例

```
🔥 P0 Hermes进程
❌ 进程挂了
详情: 未找到 Hermes 进程

🤖 全能守护者健康报告
🕐 2026-06-13 15:30
🌐 公网IP: 123.xxx.xxx.xxx
✅ Hermes进程: up
✅ 浏览器: up
✅ 磁盘空间: ok
✅ 数据库: up
✅ 网络: up
✅ 定时任务: up
🤖 自动恢复: 无异常
```

## 环境要求

- Python 3.8+
- Node.js 16+（仅部署时需要）
- Hermes Agent（被监控对象）
- AdsPower（可选，浏览器监控需要）
