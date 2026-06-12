#!/bin/bash
# Hermes Full Health Check — 完整体检 + 飞书卡片报告
set -euo pipefail

# === CONFIG: 通过环境变量覆盖，否则自动检测 ===
HERMES_HOME="${HERMES_HOME:-}"
if [ -z "$HERMES_HOME" ]; then
    if [ -f "$HOME/.hermes/config.yaml" ]; then
        HERMES_HOME="$HOME/.hermes"
    elif [ -d "$HOME/AppData/Roaming/cn.org.hermesagent.desktop/runtime/hermes-home" ]; then
        HERMES_HOME="$HOME/AppData/Roaming/cn.org.hermesagent.desktop/runtime/hermes-home"
    fi
fi
WEBHOOK_FILE="${WEBHOOK_FILE:-$HOME/.hermes/scripts/.report_webhook}"
GATEWAY_RUNTIME="$(dirname "$HERMES_HOME")/gateway-runtime"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# Hermes 二进制: 自动找最新版本
HERMES_BIN="$(find "$(dirname "$HERMES_HOME")/versions" -name "hermes-agent-cn-runtime-*.exe" 2>/dev/null | sort -V | tail -1 || echo "N/A")"

# IP探测: 默认关闭
public_ip="N/A"; ip_location=""
if [ "${ENABLE_IP_CHECK:-0}" = "1" ]; then
    public_ip=$(curl -s --connect-timeout 5 ipinfo.io/ip 2>/dev/null || echo "N/A")
    ip_location=$(curl -s --connect-timeout 5 "http://ip-api.com/json/?lang=zh-CN" 2>/dev/null | grep -oE '"(country|regionName|city)":"[^"]*"' | cut -d'"' -f4 | paste -sd' ' 2>/dev/null || echo "")
fi

# 检测项
gw_status="❓"; disk_info=""; mem_info=""; lock_info=""; cron_info=""; log_info=""; ver_info=""

if [ -f "$GATEWAY_RUNTIME/gateway_state.json" ]; then
    gw_pid=$(grep -o '"pid"[[:space:]]*:[[:space:]]*[0-9]*' "$GATEWAY_RUNTIME/gateway_state.json" 2>/dev/null | grep -o '[0-9]*' | head -1)
    if [ -n "$gw_pid" ] && tasklist 2>/dev/null | grep -q "$gw_pid"; then
        gw_status="🟢 运行中 (PID $gw_pid)"
    else
        gw_status="🔴 进程已死"
    fi
else
    gw_status="🔴 状态文件缺失"
fi

disk_used=$(df "$HOME" 2>/dev/null | awk 'NR==2 {gsub(/%/,""); print $5}')
if [ -n "$disk_used" ]; then
    if [ "$disk_used" -gt 85 ]; then color="🔴"; elif [ "$disk_used" -gt 70 ]; then color="🟡"; else color="🟢"; fi
    disk_info="$color ${disk_used}%"
fi

mem_kb=$(tasklist 2>/dev/null | grep -i "hermes-agent" | awk '{sum+=$5} END {print int(sum/1024)}')
if [ -n "$mem_kb" ] && [ "$mem_kb" -gt 0 ]; then
    if [ "$mem_kb" -gt 2048 ]; then color="🟡"; else color="🟢"; fi
    mem_info="$color ${mem_kb}MB"
fi

lock_count=$(find "$GATEWAY_RUNTIME" "$HERMES_HOME" -maxdepth 3 -name "*.lock" 2>/dev/null | wc -l | tr -d '[:space:]')
if [ "${lock_count:-0}" -eq 0 ]; then lock_info="🟢 0"; elif [ "${lock_count:-0}" -le 2 ]; then lock_info="🟢 ${lock_count:-0}"; else lock_info="🟡 ${lock_count:-0}"; fi

cron_count=$(grep -c '"name"' "$HERMES_HOME/cron/jobs.json" 2>/dev/null || echo "N/A")
if [ "$cron_count" != "N/A" ] && [ "$cron_count" -ge 2 ]; then cron_info="🟢 $cron_count"; elif [ "$cron_count" != "N/A" ]; then cron_info="🟡 $cron_count"; else cron_info="N/A"; fi

log_errs=$(tail -200 "$HERMES_HOME/logs/agent.log" 2>/dev/null | grep -ci "error\|ERROR\|panic\|fatal" || echo "0")
if [ "${log_errs:-0}" -eq 0 ]; then log_info="🟢 0"; elif [ "${log_errs:-0}" -le 5 ]; then log_info="🟡 ${log_errs:-0}"; else log_info="🔴 ${log_errs:-0}"; fi

if [ -f "$HERMES_BIN" ]; then
    ver_info="$(basename "$(dirname "$HERMES_BIN")")"
else
    ver_info="N/A"
fi

# 健康评分
score=100; [ "$gw_status" != "🔴"* ] || score=$((score-40)); [ "${lock_count:-0}" -le 2 ] || score=$((score-20))
[ -z "$disk_used" ] || [ "$disk_used" -le 85 ] || score=$((score-20)); [ "${log_errs:-0}" -le 5 ] || score=$((score-20))

if [ $score -ge 80 ]; then color="green"; elif [ $score -ge 60 ]; then color="yellow"; else color="red"; fi

card_body="**Hermes 健康体检报告**\n评分: **$score/100**\n\n"
card_body+="Gateway: $gw_status\n磁盘: $disk_info\n内存: $mem_info\n锁文件: $lock_info\nCron任务: $cron_info\n日志异常: $log_info\n版本: $ver_info"

loc_note="Monitor · $NOW"
if [ -n "$ip_location" ]; then loc_note="Monitor · $NOW · 🌐 $public_ip（$ip_location）"; fi

# 发送飞书卡片
if [ -f "$WEBHOOK_FILE" ]; then
    url=$(cat "$WEBHOOK_FILE")
    set +x
    cat > /tmp/hermes-card.json <<JSONEOF
{"msg_type":"interactive","card":{"header":{"title":{"tag":"plain_text","content":"🏥 Hermes 健康体检"},"template":"$color"},"elements":[{"tag":"markdown","content":"$card_body"},{"tag":"note","elements":[{"tag":"plain_text","content":"$loc_note"}]}]}}
JSONEOF
    curl -s -X POST -H "Content-Type: application/json" -d @/tmp/hermes-card.json "$url" > /dev/null 2>&1 || true
    rm -f /tmp/hermes-card.json
    set -x 2>/dev/null || true
fi

echo "=== Hermes Full Health Check ==="
echo "Gateway: $gw_status"
echo "Disk: $disk_info"
echo "Memory: $mem_info"
echo "Locks: $lock_info"
echo "Cron: $cron_info"
echo "Log Errors: $log_info"
echo "Score: $score/100"
