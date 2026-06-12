#!/bin/bash
# Hermes Health Monitor (fast) — 每 30 分钟探针 + 飞书告警
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
GATEWAY_RUNTIME="$(dirname "$HERMES_HOME")/gateway-runtime"
WEBHOOK_FILE="${WEBHOOK_FILE:-$HOME/.hermes/scripts/.report_webhook}"
STATE_FILE="$GATEWAY_RUNTIME/gateway_state.json"
TMP_STATE="${TMP_STATE:-/tmp/hermes-monitor-state.txt}"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# IP探测: 默认关闭
public_ip="N/A"; ip_location=""
if [ "${ENABLE_IP_CHECK:-0}" = "1" ]; then
    public_ip=$(curl -s --connect-timeout 5 ipinfo.io/ip 2>/dev/null || echo "N/A")
    ip_location=$(curl -s --connect-timeout 5 "http://ip-api.com/json/?lang=zh-CN" 2>/dev/null | grep -oE '"(country|regionName|city)":"[^"]*"' | cut -d'"' -f4 | paste -sd' ' 2>/dev/null || echo "")
fi

send_alert() {
    local title="$1" content="$2" color="$3"
    if [ ! -f "$WEBHOOK_FILE" ]; then return; fi
    local url loc_note
    url=$(cat "$WEBHOOK_FILE")
    if [ -n "$ip_location" ]; then
        loc_note="Monitor · $NOW · $public_ip（$ip_location）"
    else
        loc_note="Monitor · $NOW"
    fi
    set +x
    cat > /tmp/hermes-monitor-alert.json <<JSONEOF
{"msg_type":"interactive","card":{"header":{"title":{"tag":"plain_text","content":"$title"},"template":"$color"},"elements":[{"tag":"markdown","content":"$content"},{"tag":"note","elements":[{"tag":"plain_text","content":"$loc_note"}]}]}}
JSONEOF
    curl -s -X POST -H "Content-Type: application/json" -d @/tmp/hermes-monitor-alert.json "$url" > /dev/null 2>&1 || true
    rm -f /tmp/hermes-monitor-alert.json
    set -x 2>/dev/null || true
}

issues=""

# P0: Gateway
if [ -f "$STATE_FILE" ]; then
    gw_pid=$(grep -o '"pid"[[:space:]]*:[[:space:]]*[0-9]*' "$STATE_FILE" 2>/dev/null | grep -o '[0-9]*' | head -1)
    if [ -n "$gw_pid" ] && tasklist 2>/dev/null | grep -q "$gw_pid"; then
        : # OK
    else
        issues+="- Gateway PID 已死\n"
    fi
else
    issues+="- gateway_state.json 不存在\n"
fi

# P1: Lock files
lock_count=$(find "$GATEWAY_RUNTIME" "$HERMES_HOME" -maxdepth 3 -name "*.lock" 2>/dev/null | wc -l | tr -d '[:space:]')
if [ "${lock_count:-0}" -gt 2 ]; then
    issues+="- 残留锁文件: ${lock_count:-0}个\n"
fi

# P2: Disk
disk_pct=$(df "$HOME" 2>/dev/null | awk 'NR==2 {gsub(/%/,""); print $5}')
if [ -n "$disk_pct" ] && [ "$disk_pct" -gt 85 ]; then
    issues+="- 磁盘使用率: ${disk_pct}%\n"
fi

if [ -n "$issues" ]; then
    if [ ! -f "$TMP_STATE" ] || [ "$(cat "$TMP_STATE" 2>/dev/null)" != "ALERT" ]; then
        echo "ALERT" > "$TMP_STATE"
        send_alert "Hermes 健康告警" "$issues" "red"
    fi
    echo "[$(date '+%H:%M:%S')] ISSUES:"
    echo -e "$issues"
else
    if [ -f "$TMP_STATE" ] && [ "$(cat "$TMP_STATE" 2>/dev/null)" = "ALERT" ]; then
        echo "OK" > "$TMP_STATE"
        send_alert "Hermes 已恢复" "所有检查通过" "green"
    fi
    echo "[$(date '+%H:%M:%S')] All checks passed"
fi
