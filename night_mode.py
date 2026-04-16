"""
🌙 NIGHT MODE 2030 ADVANCED — Graceful shutdown + soft resume
✅ Улучшения:
- Graceful shutdown браузера с сохранением cookies, localStorage, sessionStorage
- Soft resume браузера после ночи (5-10 мин спокойного поведения)
- Полная поддержка асинхронных операций
- Правильный JSON сохранить/загрузить
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
import asyncio

from playwright.async_api import Page, BrowserContext
from colorama import Fore, Style

from config.settings import settings


class NightMode:
    """🌙 Управление ночным режимом с graceful shutdown и soft resume"""

    def __init__(self, logger, notifier=None):
        self.logger = logger
        self.notifier = notifier
        
        self.overrides: Dict[str, float] = {}
        self.suspended_accounts: Dict[str, Dict] = {}
        
        self.session_storage_path = Path("storage/night_mode_sessions")
        self.session_storage_path.mkdir(parents=True, exist_ok=True)

    def get_night_schedule(self) -> tuple:
        """Получить расписание ночного режима (с рандомизацией)"""
        base_start = settings.night_mode_start[0]
        base_end = settings.night_mode_end[0]
        
        random_offset_start = random.randint(-60, 60)
        random_offset_end = random.randint(-60, 60)
        
        offset_start_hours = random_offset_start // 60
        offset_end_hours = random_offset_end // 60
        
        actual_start = (base_start + offset_start_hours) % 24
        actual_end = (base_end + offset_end_hours) % 24
        
        return (int(actual_start), int(actual_end))

    def can_work(self, account_id: str) -> bool:
        """Может ли аккаунт работать сейчас?"""
        
        # Проверяем override
        if account_id in self.overrides:
            override_end = self.overrides[account_id]
            if datetime.now().timestamp() < override_end:
                return True
            else:
                del self.overrides[account_id]

        # Проверяем ночной режим
        current_hour = datetime.now().hour
        night_start, night_end = self.get_night_schedule()

        if night_start <= night_end:
            return not (night_start <= current_hour < night_end)
        else:
            return not (current_hour >= night_start or current_hour < night_end)

    async def graceful_shutdown(
        self,
        account_id: str,
        page: Page,
        context: Optional[BrowserContext] = None,
    ) -> Dict:
        """
        Graceful shutdown браузера с сохранением ВСЕГО
        
        Сохраняет:
        - cookies
        - localStorage
        - sessionStorage
        """
        
        shutdown_data = {
            "account_id": account_id,
            "shutdown_timestamp": datetime.now().isoformat(),
            "cookies": [],
            "local_storage": {},
            "session_storage": {},
        }

        try:
            # ─── СОХРАНЯЕМ COOKIES ───
            if context:
                cookies = await context.cookies()
                shutdown_data["cookies"] = cookies
                self.logger.info(account_id, f"💾 Сохранено {len(cookies)} cookies")

            # ─── СОХРАНЯЕМ localStorage ───
            try:
                local_storage = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            storage[key] = localStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
                shutdown_data["local_storage"] = local_storage
                self.logger.info(account_id, f"💾 Сохранено {len(local_storage)} localStorage items")
            except Exception as e:
                self.logger.warning(account_id, f"localStorage save error: {e}")

            # ─── СОХРАНЯЕМ sessionStorage ───
            try:
                session_storage = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            storage[key] = sessionStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
                shutdown_data["session_storage"] = session_storage
                self.logger.info(account_id, f"💾 Сохранено {len(session_storage)} sessionStorage items")
            except Exception as e:
                self.logger.warning(account_id, f"sessionStorage save error: {e}")

            # ─── СОХРАНЯЕМ НА ДИСК ───
            session_file = self.session_storage_path / f"{account_id}_session.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(shutdown_data, f, indent=2, ensure_ascii=False)

            self.suspended_accounts[account_id] = shutdown_data

            print(f"\n  {Fore.BLUE}💤 Graceful shutdown для {account_id}{Style.RESET_ALL}")
            print(f"     💾 Сохранено: {len(shutdown_data['cookies'])} cookies, {len(shutdown_data['local_storage'])} localStorage, {len(shutdown_data['session_storage'])} sessionStorage")

            return shutdown_data

        except Exception as e:
            self.logger.error(account_id, f"Graceful shutdown error: {e}", severity="HIGH")
            return shutdown_data

    async def soft_resume(
        self,
        account_id: str,
        page: Page,
        context: Optional[BrowserContext] = None,
    ) -> bool:
        """
        Soft resume после ночи (восстановление сессии)
        
        Восстанавливает:
        - cookies
        - localStorage
        - sessionStorage
        """
        
        try:
            # ─── ЗАГРУЖАЕМ СОХРАНЁННУЮ СЕССИЮ ───
            session_file = self.session_storage_path / f"{account_id}_session.json"
            
            if not session_file.exists():
                self.logger.warning(account_id, "Сохранённая сессия не найдена")
                return False

            with open(session_file, 'r', encoding='utf-8') as f:
                shutdown_data = json.load(f)

            # ─── ВОССТАНАВЛИВАЕМ COOKIES ───
            if shutdown_data.get("cookies") and context:
                try:
                    await context.add_cookies(shutdown_data["cookies"])
                    self.logger.info(account_id, f"✅ Восстановлено {len(shutdown_data['cookies'])} cookies")
                except Exception as e:
                    self.logger.warning(account_id, f"Cookies restore error: {e}")

            # ─── ВОССТАНАВЛИВАЕМ localStorage ───
            if shutdown_data.get("local_storage"):
                local_storage_script = """
                    (data) => {
                        for (const [key, value] of Object.entries(data)) {
                            try {
                                localStorage.setItem(key, value);
                            } catch (e) {}
                        }
                    }
                """
                try:
                    await page.evaluate(local_storage_script, shutdown_data["local_storage"])
                    self.logger.info(account_id, f"✅ Восстановлено {len(shutdown_data['local_storage'])} localStorage items")
                except Exception as e:
                    self.logger.warning(account_id, f"localStorage restore error: {e}")

            # ─── ВОССТАНАВЛИВАЕМ sessionStorage ───
            if shutdown_data.get("session_storage"):
                session_storage_script = """
                    (data) => {
                        for (const [key, value] of Object.entries(data)) {
                            try {
                                sessionStorage.setItem(key, value);
                            } catch (e) {}
                        }
                    }
                """
                try:
                    await page.evaluate(session_storage_script, shutdown_data["session_storage"])
                    self.logger.info(account_id, f"✅ Восстановлено {len(shutdown_data['session_storage'])} sessionStorage items")
                except Exception as e:
                    self.logger.warning(account_id, f"sessionStorage restore error: {e}")

            # ─── SOFT RESUME: 5 МИНУТ СПОКОЙНОГО ПОВЕДЕНИЯ ───
            print(f"\n  {Fore.GREEN}🌅 Soft resume для {account_id} (5 мин спокойного поведения){Style.RESET_ALL}")
            
            soft_resume_duration = 5 * 60
            await asyncio.sleep(soft_resume_duration)

            if self.notifier:
                try:
                    await self.notifier.notify_night_mode_wake_up(account_id)
                except Exception:
                    pass

            return True

        except Exception as e:
            self.logger.error(account_id, f"Soft resume error: {e}", severity="MEDIUM")
            return False

    def override(self, account_id: str, hours: float):
        """Временно отключить ночной режим"""
        override_seconds = hours * 3600
        override_end = datetime.now().timestamp() + override_seconds
        self.overrides[account_id] = override_end
        
        self.logger.success(account_id, f"🌙 Ночь отключена на {hours:.1f} часов")
        
        if self.notifier:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        self.notifier.notify_night_override(account_id, hours)
                    )
                else:
                    loop.run_until_complete(
                        self.notifier.notify_night_override(account_id, hours)
                    )
            except Exception as e:
                self.logger.warning(account_id, f"Override notify error: {e}")

    def reset_override(self, account_id: str):
        """Вернуть ночной режим"""
        if account_id in self.overrides:
            del self.overrides[account_id]
            self.logger.success(account_id, "🌙 Ночной режим восстановлен")

    def get_status(self, account_id: str) -> Dict:
        """Получить статус ночного режима"""
        can_work = self.can_work(account_id)
        current_hour = datetime.now().hour
        night_start, night_end = self.get_night_schedule()
        
        override_active = account_id in self.overrides
        override_end = None
        if override_active:
            override_end = datetime.fromtimestamp(
                self.overrides[account_id]
            ).isoformat()

        return {
            "can_work": can_work,
            "current_hour": current_hour,
            "night_start": f"{night_start:02d}:00",
            "night_end": f"{night_end:02d}:00",
            "override_active": override_active,
            "override_end": override_end,
            "is_suspended": account_id in self.suspended_accounts,
        }

    def print_status(self, account_ids: list):
        """Вывести статус ночного режима"""
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🌙 НОЧНОЙ РЕЖИМ':^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

        for acc_id in account_ids:
            status = self.get_status(acc_id)
            can_work = "✅ может работать" if status["can_work"] else "❌ спит"
            override = (
                f"⏰ override до {status['override_end']}"
                if status["override_active"]
                else "нет override"
            )
            print(f"  {Fore.YELLOW}{acc_id}{Style.RESET_ALL}")
            print(f"    Время: {status['current_hour']:02d}:00")
            print(f"    Статус: {can_work}")
            print(f"    Override: {override}")
            print()

        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")