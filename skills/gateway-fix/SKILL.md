---
name: hermes-gateway-fix
description: "修复 Hermes Gateway 静默崩溃后飞书不对话的问题"
---

# Hermes Gateway 崩溃修复

## 症状

- 飞书（或其他平台）突然不回复消息
- 桌面版还在运行，但 gateway 无响应

## 快速诊断

```bash
# 1. 检查 gateway 进程
cat gateway-runtime/gateway_state.json   # 看 PID
tasklist | grep <PID>                    # 验活

# 2. 检查锁文件
find gateway-runtime/ hermes-home/ -name "*.lock" -o -name "*.pid"

# 3. 看日志
tail -30 logs/gateway.log
```

## 一键修复

```bash
# 清理僵尸状态
rm -f gateway-runtime/gateway_state.json
rm -f gateway-runtime/token-locks/feishu-*.lock

# 重启 gateway（从 hermes-home 目录）
export HERMES_HOME="$(pwd)"
export HERMES_GATEWAY_RUNTIME_DIR="$(dirname $(pwd))/gateway-runtime"
"../versions/$(cat ../current.json | grep runtimeVersion | cut -d'"' -f4)/hermes-agent-cn-runtime-win32-x64.exe" -m hermes_cli.main gateway run &

# 等5秒验证
sleep 5 && cat ../gateway-runtime/gateway_state.json
```

## 典型故障模式

| 症状 | 原因 | 修复 |
|------|------|------|
| `gateway_state.json` 标记 running 但进程已死 | Gateway 静默崩溃 | 清理 json + 重启 |
| `gateway.lock` 残留 | 异常退出未清理 | 删除锁文件 |
| 飞书 token lock 残留 | Token 刷新时崩溃 | 删除 feishu-*.lock |
