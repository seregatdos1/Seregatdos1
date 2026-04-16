# config/settings.py
"""
⚙️ SETTINGS — Полная конфигурация проекта из .env
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


def _parse_time(time_str: str) -> Tuple[int, int]:
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 23, 7


def _parse_accounts() -> Dict[str, dict]:
    accounts = {}
    for i in range(1, 11):
        raw = os.getenv(f"ACCOUNT_{i}", "").strip()
        if raw and ":" in raw:
            phone, password = raw.split(":", 1)
            accounts[f"account_{i}"] = {
                "id": f"account_{i}",
                "index": i,
                "phone": phone.strip(),
                "password": password.strip(),
                "name": os.getenv(f"ACCOUNT_{i}_NAME", f"Аккаунт #{i}").strip(),
            }
            continue

        phone = os.getenv(f"ACCOUNT_{i}_PHONE", "").strip()
        if phone:
            accounts[f"account_{i}"] = {
                "id": f"account_{i}",
                "index": i,
                "phone": phone,
                "password": "",
                "name": os.getenv(f"ACCOUNT_{i}_NAME", f"Аккаунт #{i}").strip(),
            }

    return accounts


def _parse_proxies() -> Dict[str, dict]:
    proxies = {}
    for i in range(1, 11):
        raw = os.getenv(f"PROXY_{i}", "").strip().strip("'\"")
        if not raw:
            continue

        proxy = _parse_single_proxy(raw, index=i)
        if proxy:
            proxies[f"proxy_{i}"] = proxy
    return proxies


def _parse_single_proxy(raw: str, index: int) -> Optional[dict]:
    if "://" in raw:
        from urllib.parse import urlparse
        parsed = urlparse(raw)
        return {
            "index": index,
            "protocol": parsed.scheme or "http",
            "host": parsed.hostname or "",
            "port": parsed.port or 0,
            "username": parsed.username or "",
            "password": parsed.password or "",
            "raw": raw,
        }

    parts = raw.split(":")
    if len(parts) == 4:
        try:
            return {
                "index": index,
                "protocol": "http",
                "host": parts[0],
                "port": int(parts[1]),
                "username": parts[2],
                "password": parts[3],
                "raw": raw,
            }
        except ValueError:
            return None

    if len(parts) == 2:
        try:
            return {
                "index": index,
                "protocol": "http",
                "host": parts[0],
                "port": int(parts[1]),
                "username": "",
                "password": "",
                "raw": raw,
            }
        except ValueError:
            return None

    return None


@dataclass
class Settings:
    project_root: Path = PROJECT_ROOT
    storage_dir: Path = PROJECT_ROOT / "storage"
    sessions_dir: Path = PROJECT_ROOT / "storage" / "sessions"
    logs_dir: Path = PROJECT_ROOT / "storage" / "logs"
    data_dir: Path = PROJECT_ROOT / "storage" / "data"

    accounts: Dict[str, dict] = field(default_factory=_parse_accounts)
    proxies: Dict[str, dict] = field(default_factory=_parse_proxies)

    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )
    telegram_chat_id: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", "")
    )
    telegram_enabled: bool = False
    tg_notify_login: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_LOGIN", "true").lower() == "true"
    )
    tg_notify_warmup: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_WARMUP", "true").lower() == "true"
    )
    tg_notify_ban: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_BAN", "true").lower() == "true"
    )
    tg_notify_captcha: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_CAPTCHA", "true").lower() == "true"
    )
    tg_notify_proxy_down: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_PROXY_DOWN", "true").lower() == "true"
    )

    warmup_duration_minutes: int = field(
        default_factory=lambda: int(os.getenv("WARMUP_DURATION_MINUTES", "90"))
    )
    warmup_categories: List[str] = field(
        default_factory=lambda: [
            c.strip()
            for c in os.getenv(
                "WARMUP_CATEGORIES", "мототехника,питбайки,квадроциклы"
            ).split(",")
        ]
    )

    max_actions_per_hour: int = field(
        default_factory=lambda: int(os.getenv("MAX_ACTIONS_PER_HOUR", "8"))
    )
    max_actions_per_day: int = field(
        default_factory=lambda: int(os.getenv("MAX_ACTIONS_PER_DAY", "100"))
    )
    night_mode_start: Tuple[int, int] = field(
        default_factory=lambda: _parse_time(os.getenv("NIGHT_MODE_START", "23:00"))
    )
    night_mode_end: Tuple[int, int] = field(
        default_factory=lambda: _parse_time(os.getenv("NIGHT_MODE_END", "07:00"))
    )
    circuit_breaker_threshold: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    )
    circuit_breaker_cooldown_minutes: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_COOLDOWN_MINUTES", "30"))
    )

    headless: bool = field(
        default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true"
    )
    page_load_timeout: int = field(
        default_factory=lambda: int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    )

    def __post_init__(self):
        for dir_path in [self.storage_dir, self.sessions_dir, self.logs_dir, self.data_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.telegram_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)

    def print_summary(self):
        from colorama import Fore, Style
        print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'⚙️  КОНФИГУРАЦИЯ':^70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"  Аккаунтов:       {Fore.GREEN}{len(self.accounts)}{Style.RESET_ALL}")
        for acc_id, acc in self.accounts.items():
            proxy = self.get_proxy_for_account(acc_id)
            proxy_str = f"{proxy['host']}:{proxy['port']}" if proxy else "❌ нет"
            print(f"    {acc_id}: {acc['phone']} → {proxy_str}")
        print(f"  Прокси:           {Fore.GREEN}{len(self.proxies)}{Style.RESET_ALL}")
        print(f"  Telegram:         {'✅' if self.telegram_enabled else '❌'}")
        print(f"  Ночной режим:     {self.night_mode_start[0]:02d}:{self.night_mode_start[1]:02d} — {self.night_mode_end[0]:02d}:{self.night_mode_end[1]:02d}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

    def get_proxy_for_account(self, account_id: str) -> Optional[dict]:
        if not self.proxies:
            return None
        try:
            acc_index = int(account_id.split("_")[1])
            proxy_key = f"proxy_{acc_index}"
            if proxy_key in self.proxies:
                return self.proxies[proxy_key]
            proxy_keys = sorted(self.proxies.keys())
            if proxy_keys:
                fallback_key = proxy_keys[(acc_index - 1) % len(proxy_keys)]
                return self.proxies[fallback_key]
        except Exception:
            pass
        return None


settings = Settings()