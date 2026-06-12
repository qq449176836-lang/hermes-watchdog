"""状态管理 — 加载/保存检查状态 & 事件日志"""
import json
import os
from datetime import datetime

from .config import get_scripts_dir


def _state_file():
    return os.path.join(get_scripts_dir(), ".monitor_state.json")


def _log_file():
    return os.path.join(get_scripts_dir(), ".monitor_log.jsonl")


def load_state():
    """加载上次检查状态"""
    sf = _state_file()
    if os.path.isfile(sf):
        with open(sf) as f:
            return json.load(f)
    return {"checks": {}, "last_p0": None, "last_p1": None, "recovery_count": 0}


def save_state(state):
    """保存检查状态"""
    sf = _state_file()
    os.makedirs(os.path.dirname(sf), exist_ok=True)
    with open(sf, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def log_event(level, check, msg, recovered=False):
    """追加一条事件日志"""
    lf = _log_file()
    os.makedirs(os.path.dirname(lf), exist_ok=True)
    entry = json.dumps({
        "time": datetime.now().isoformat(),
        "level": level,
        "check": check,
        "msg": msg,
        "recovered": recovered,
    }, ensure_ascii=False)
    with open(lf, "a") as f:
        f.write(entry + "\n")
