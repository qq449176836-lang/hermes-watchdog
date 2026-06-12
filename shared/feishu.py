"""飞书通知 — 统一的消息推送"""
import json
import urllib.request


def notify(webhook, level, title, body):
    """通过飞书 Webhook 发送分级通知"""
    if not webhook:
        print(f"[{level}] {title}: {body}")
        return

    emoji = {"P0": "\U0001f6a8", "P1": "\u26a0\ufe0f", "P2": "\U0001f514", "P3": "\u2139\ufe0f"}
    tag =  {"P0": "@all", "P1": "", "P2": "", "P3": ""}

    text = f"{emoji.get(level, '\U0001f4cb')} [{level}] {title}\n\n{body}\n{tag.get(level, '')}"
    payload = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False).encode()

    try:
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[Feishu] {level} 推送完成")
    except Exception as e:
        print(f"[Feishu] 推送失败: {e}")
