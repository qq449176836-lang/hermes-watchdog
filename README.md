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
├── shared/                            # Python 共享模块
│   ├── config.py                      # 配置 & Hermes 版本自动检测
│   ├── checks.py                      # 健康探针 & 自动恢复
│   ├── state.py                       # JSON 状态持久化
│   └── feishu.py                      # 飞书通知
├── scripts/                           # 独立 Bash 脚本（零依赖）
│   ├── health-monitor.sh              # 快速探针（30min，去重告警）
│   └── full-check.sh                  # 完整体检（飞书卡片报告）
└── skills/                            # Hermes 技能包
    ├── monitor/                       # Python 监控引擎 + 部署
    │   ├── deploy.cjs                 # 一键部署脚本
    │   ├── monitor.py                 # 核心引擎
    │   └── README.md
    └── gateway-fix/                   # Gateway 崩溃修复 SOP
        └── SKILL.md
```

## 检测维度

| 探针 | 频率 | 级别 | 说明 |
|------|------|------|------|
| Hermes 进程 | 30min | **P0** | Hermes 桌面端是否在运行 |
| AdsPower 浏览器 | 30min | **P1** | 广告采集依赖的浏览器状态 |
| 磁盘空间 | 2h | **P2** | 磁盘是否即将写满 |
| 数据库可读写 | 30min | **P1** | 核心数据库是否正常 |
| 公网网络 | 30min | **P2** | 外网连通性 |
| Cron 任务完整性 | 2h | **P1** | 定时任务是否丢失 |

## 告警分级

| 级别 | 含义 | 飞书动作 | 自动恢复 |
|------|------|----------|----------|
| 🚨 **P0** | 核心服务不可用 | @所有人 | 自动重启 |
| ⚠️ **P1** | 功能异常 | 普通通知 | 自动修复 |
| 🔔 **P2** | 需关注 | 通知 | 记录待处理 |
| ℹ️ **P3** | 信息 | 通知 | 仅记录 |

## 配置方式

```bash
# 飞书 Webhook（二选一）
# 选项A：环境变量
export FEISHU_BOT_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/your_token_here

# 选项B：配置文件（推荐）
cp config/webhook.example ~/.hermes/scripts/.report_webhook
# 编辑 .report_webhook 填入你的 Webhook URL

# 测试监控
cd skills/monitor && python monitor.py
```

## 环境要求

- Python 3.8+
- Node.js 16+（deploy.cjs 需要）
- Windows 10/11（Hermes Agent 运行环境）
- 飞书机器人 Webhook（告警推送）

## 从 hermes-monitor 迁移

本仓库是原 `hermes-monitor` 的独立版。如果之前使用旧版：
- 配置文件和运行状态在 `~/.hermes/scripts/.report_webhook`
- 迁移后所有功能不变，部署脚本已更新指向新仓库地址

---

*Hermes Watchdog — 让你的 Agent 永不掉线*
