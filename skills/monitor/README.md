# Monitor — 全能守护者

Hermes Agent 健康监控技能：分级告警 + 探针检测 + 自动恢复 + 去重通知。

## 安装

```bash
node deploy.cjs
```

或让 Hermes 执行一句话：

> 把 `skills/monitor/` 目录复制到 `~/.hermes/scripts/`，然后 `node ~/.hermes/scripts/deploy.cjs`

## 检测维度

| 探针 | 频率 | 级别 |
|------|------|------|
| Hermes 进程 | 30min | P0 |
| AdsPower 浏览器 | 30min | P1 |
| 磁盘空间 | 2h | P2 |
| 数据库可读写 | 30min | P1 |
| 公网网络 | 30min | P2 |
| Cron 任务完整性 | 2h | P1 |

## 告警分级

| 级别 | 触发条件 | 动作 |
|------|----------|------|
| P0 | Hermes 进程挂 | @all + 自动重启 |
| P1 | 浏览器/DB/Cron 异常 | 飞书通知 + 自动恢复 |
| P2 | 磁盘/网络波动 | 飞书通知 |

## 配置

- 飞书 Webhook：写入 `~/.hermes/scripts/.report_webhook`
- AdsPower 环境变量：`ADS_PROFILE` 或 `ADS_API`
