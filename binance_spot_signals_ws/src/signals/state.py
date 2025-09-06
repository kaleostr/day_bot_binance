
from __future__ import annotations
from typing import Dict, Tuple
from datetime import datetime, timedelta, timezone

class SignalState:
    def __init__(self, cooldown_minutes: int = 10) -> None:
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.sent: Dict[Tuple[str, str], datetime] = {}
        self.last_by_symbol_dir: Dict[Tuple[str, str], datetime] = {}

    def can_send(self, key: Tuple[str, str], bar_dt: datetime) -> bool:
        uniq_key = (f"{key[0]}_{key[1]}_{int(bar_dt.timestamp())}", "k")
        now = datetime.now(timezone.utc)
        last_any = self.last_by_symbol_dir.get(key)
        if last_any and now - last_any < self.cooldown:
            return False
        if uniq_key in self.sent:
            return False
        return True

    def mark_sent(self, key: Tuple[str, str], bar_dt: datetime) -> None:
        uniq_key = (f"{key[0]}_{key[1]}_{int(bar_dt.timestamp())}", "k")
        now = datetime.now(timezone.utc)
        self.sent[uniq_key] = now
        self.last_by_symbol_dir[key] = now
