# core/browser/launcher.py
"""
🌐 BROWSER LAUNCHER 2030 — МАКСИМАЛЬНАЯ УСТОЙЧИВОСТЬ К ПЛОХИМ ПРОКСИ
Агрессивный retry, fallback, recovery, timeout management
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import time
import random

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from colorama import Fore, Style

from core.browser.fingerprint import Fingerprint, FingerprintStore
from core.browser.stealth import build_stealth_script
from config.settings import settings


class BrowserLauncher:
    """🌐 Browser Launcher 2030 — Production ready"""

    # ════════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ════════════════════════════════════════════════════════════════
    
    CONTEXT_CREATE_RETRIES = 5  # Было 3, теперь 5 попыток
    CONTEXT_CREATE_TIMEOUT = 45  # Было 30, теперь 45 сек
    CONTEXT_CREATE_INITIAL_WAIT = 3  # Начальная пауза перед первой попыткой
    
    PAGE_GOTO_TIMEOUT = 25000  # Было 20000, теперь 25 сек
    PAGE_GOTO_RETRIES = 3  # Было 2, теперь 3 попытки
    PAGE_GOTO_WAIT_UNTIL_MODES = ["domcontentloaded", "load"]  # load как fallback
    
    BROWSER_RECOVERY_TIMEOUT = 10  # Timeout для recovery процесса
    BROWSER_RECOVERY_MAX_ATTEMPTS = 2

    def __init__(self, logger, proxy_manager):
        self.logger = logger
        self.proxy_manager = proxy_manager
        
        self._pw = None
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        
        self.fingerprint_store = FingerprintStore()
        
        self.sessions_dir = Path("storage/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_dir = self.sessions_dir / "cookies"
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        
        # Диагностика и статистика
        self.proxy_errors_count: Dict[str, int] = {}
        self.timeout_errors_count: Dict[str, int] = {}
        self.successful_launches: Dict[str, int] = {}
        self.browser_crash_count = 0
        self.goto_success_count: Dict[str, int] = {}
        self.goto_failure_count: Dict[str, int] = {}

    async def initialize(self):
        """Инициализация Playwright"""
        try:
            print(f"  {Fore.CYAN}🌐 Инициализирую Playwright...{Style.RESET_ALL}")
            self._pw = await async_playwright().start()
            
            # Оптимальные аргументы браузера для прокси
            args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-web-resources",
                "--disable-sync",
                "--disable-background-networking",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-translate",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-client-side-phishing-detection",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
            ]
            
            self._browser = await self._pw.chromium.launch(
                headless=settings.headless,
                args=args,
                timeout=45000,  # 45 сек на запуск браузера
            )
            
            print(f"  {Fore.GREEN}✅ Playwright инициализирован{Style.RESET_ALL}")
            self.logger.system("✅ Playwright инициализирован")
            
        except Exception as e:
            error_msg = str(e)[:200]
            print(f"  {Fore.RED}❌ Не удалось запустить браузер: {error_msg}{Style.RESET_ALL}")
            self.logger.error("launcher", f"Cannot launch browser: {e}", severity="CRITICAL")
            raise

    async def _recover_browser(self) -> bool:
        """
        Восстановить браузер после критической ошибки
        
        Returns:
            True если успешно восстановлен, False иначе
        """
        print(f"  {Fore.YELLOW}🔄 Восстанавливаю браузер после краша...{Style.RESET_ALL}")
        self.browser_crash_count += 1
        
        if self.browser_crash_count > self.BROWSER_RECOVERY_MAX_ATTEMPTS:
            print(f"  {Fore.RED}❌ Лимит попыток recovery исчерпан ({self.BROWSER_RECOVERY_MAX_ATTEMPTS}){Style.RESET_ALL}")
            return False
        
        try:
            # Закрываем старый браузер
            if self._browser:
                try:
                    await asyncio.wait_for(self._browser.close(), timeout=5)
                except Exception:
                    pass
            
            # Очищаем контексты и страницы
            self._contexts.clear()
            self._pages.clear()
            
            # Перезагружаем Playwright
            if self._pw:
                try:
                    await asyncio.wait_for(self._pw.stop(), timeout=5)
                except Exception:
                    pass
            
            self._pw = None
            self._browser = None
            
            # Пауза перед переинициализацией
            await asyncio.sleep(3)
            
            # Реинициализируем
            await self.initialize()
            print(f"  {Fore.GREEN}✅ Браузер успешно восстановлен (попытка #{self.browser_crash_count}){Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"  {Fore.RED}❌ Recovery failed: {str(e)[:100]}{Style.RESET_ALL}")
            self.logger.error("launcher", f"Browser recovery failed: {e}", severity="CRITICAL")
            return False

    async def launch(self, account_id: str) -> Optional[Page]:
        """
        Запустить браузер для аккаунта с полной обработкой ошибок
        
        Возвращает Page если успешно, None если критическая ошибка
        """
        
        if not self._browser:
            try:
                await self.initialize()
            except Exception as e:
                print(f"  {Fore.RED}❌ Не удалось инициализировать браузер: {e}{Style.RESET_ALL}")
                return None

        # Проверяем существующую страницу
        existing = self._pages.get(account_id)
        if existing:
            try:
                if not existing.is_closed():
                    return existing
            except Exception:
                pass

        try:
            fp = self.fingerprint_store.get_or_create(account_id)
            self.fingerprint_store.refresh_session_seed(account_id)
        except Exception as e:
            print(f"  {Fore.YELLOW}⚠️ Ошибка fingerprint: {e}{Style.RESET_ALL}")
            fp = None

        proxy_cfg = self.proxy_manager.get_playwright_proxy(account_id)
        proxy_info = f"{proxy_cfg.get('server', 'без прокси')}" if proxy_cfg else "без прокси"
        
        print(f"  {Fore.CYAN}🔗 Запускаю браузер для {account_id}...{Style.RESET_ALL}")
        print(f"     Прокси: {proxy_info}")

        # ════════════════════════════════════════════════════════════════
        # RETRY LOOP: Создание контекста с агрессивным retry
        # ════════════════════════════════════════════════════════════════
        
        context = None
        page = None
        
        for attempt in range(1, self.CONTEXT_CREATE_RETRIES + 1):
            try:
                # Пауза перед попыткой (особенно для первых)
                if attempt == 1:
                    await asyncio.sleep(self.CONTEXT_CREATE_INITIAL_WAIT)
                else:
                    # Exponential backoff с jitter
                    backoff = min(2 ** (attempt - 1), 16) + random.uniform(0, 2)
                    await asyncio.sleep(backoff)
                
                print(f"    [Попытка {attempt}/{self.CONTEXT_CREATE_RETRIES}] Создаю контекст...", end=" ", flush=True)
                
                context, page = await self._create_context_with_page(
                    account_id=account_id,
                    proxy_cfg=proxy_cfg,
                    fp=fp,
                    attempt=attempt
                )
                
                if context and page:
                    print(f"{Fore.GREEN}✅{Style.RESET_ALL}")
                    break
                    
            except asyncio.CancelledError:
                print(f"{Fore.YELLOW}⏸️ CANCELLED{Style.RESET_ALL}")
                
                if attempt >= 2:
                    try:
                        await self._recover_browser()
                        return await self.launch(account_id)
                    except Exception:
                        return None
                continue
                    
            except Exception as e:
                error_msg = str(e)[:120]
                print(f"{Fore.YELLOW}⚠️{Style.RESET_ALL}")
                
                # Если "connection closed" или "driver" — браузер упал
                if "connection" in error_msg.lower() or "driver" in error_msg.lower():
                    print(f"      🔴 БРАУЗЕР УПАЛ: {error_msg[:80]}")
                    
                    if attempt >= 2:
                        recovery_success = await self._recover_browser()
                        if recovery_success:
                            return await self.launch(account_id)
                        else:
                            return None
                else:
                    print(f"      ⚠️ {error_msg[:80]}")
                
                if attempt < self.CONTEXT_CREATE_RETRIES:
                    continue
                else:
                    return None

        if not context or not page:
            print(f"  {Fore.RED}❌ Не удалось создать контекст после {self.CONTEXT_CREATE_RETRIES} попыток{Style.RESET_ALL}")
            return None

        # ════════════════════════════════════════════════════════════════
        # Stealth Script
        # ════════════════════════════════════════════════════════════════
        
        try:
            if fp:
                stealth_script = build_stealth_script(fp)
                await context.add_init_script(stealth_script)
        except Exception as e:
            self.logger.warning(account_id, f"Stealth script failed: {e}")

        # ════════════════════════════════════════════════════════════════
        # Загрузка Cookies
        # ════════════════════════════════════════════════════════════════
        
        cookies = self._load_cookies(account_id)
        if cookies:
            try:
                await context.add_cookies(cookies)
                print(f"  {Fore.GREEN}✅ Cookies восстановлены ({len(cookies)} шт){Style.RESET_ALL}")
                self.logger.action(account_id, "RESTORE_COOKIES", "SUCCESS", count=len(cookies))
            except Exception as e:
                self.logger.warning(account_id, f"Cookie load failed: {e}")

        # ════════════════════════════════════════════════════════════════
        # Сохранение контекста и страницы
        # ════════════════════════════════════════════════════════════════
        
        self._contexts[account_id] = context
        self._pages[account_id] = page

        print(f"  {Fore.GREEN}✅ Браузер полностью готов: {account_id}{Style.RESET_ALL}")
        self.logger.system(f"Browser launched: {account_id}")
        
        self.successful_launches[account_id] = self.successful_launches.get(account_id, 0) + 1
        
        return page

    async def _create_context_with_page(
        self,
        account_id: str,
        proxy_cfg: Optional[Dict],
        fp: Optional[Fingerprint],
        attempt: int
    ) -> Tuple[Optional[BrowserContext], Optional[Page]]:
        """Создать контекст браузера и страницу"""
        
        try:
            context_kwargs = {
                "viewport": {"width": 1366, "height": 768},
                "locale": "ru-RU",
            }
            
            if fp:
                context_kwargs["timezone_id"] = fp.timezone
            
            if proxy_cfg:
                context_kwargs["proxy"] = proxy_cfg

            try:
                context = await asyncio.wait_for(
                    self._browser.new_context(**context_kwargs),
                    timeout=self.CONTEXT_CREATE_TIMEOUT
                )
            except asyncio.TimeoutError:
                self.timeout_errors_count[account_id] = self.timeout_errors_count.get(account_id, 0) + 1
                return None, None
            except asyncio.CancelledError:
                raise

            try:
                page = await asyncio.wait_for(
                    context.new_page(),
                    timeout=15
                )
            except Exception as e:
                await context.close()
                return None, None

            return context, page

        except Exception as e:
            error_msg = str(e)[:150]
            
            if "proxy" in error_msg.lower() or "ERR_PROXY" in error_msg:
                self.proxy_errors_count[account_id] = self.proxy_errors_count.get(account_id, 0) + 1
            
            raise

    async def goto_safe(
        self,
        page: Page,
        account_id: str,
        url: str,
        wait_until: str = "domcontentloaded"
    ) -> bool:
        """
        Максимально устойчивая навигация на URL
        
        Особенности:
        - 3 попытки с exponential backoff
        - Fallback на другой wait_until режим
        - Хорошая обработка ошибок
        - Не падает при прокси ошибке
        """
        
        wait_modes = [wait_until]
        
        # Добавляем fallback режимы
        if wait_until not in self.PAGE_GOTO_WAIT_UNTIL_MODES:
            wait_modes.extend(self.PAGE_GOTO_WAIT_UNTIL_MODES)
        
        for retry_attempt in range(1, self.PAGE_GOTO_RETRIES + 1):
            for wait_idx, wait_mode in enumerate(wait_modes):
                try:
                    print(f"    → {url[:55]:55} ", end="", flush=True)
                    
                    goto_timeout = self.PAGE_GOTO_TIMEOUT + (retry_attempt * 5000)  # +5сек за каждую попытку
                    
                    await asyncio.wait_for(
                        page.goto(
                            url,
                            wait_until=wait_mode,
                            timeout=self.PAGE_GOTO_TIMEOUT
                        ),
                        timeout=(goto_timeout / 1000)
                    )
                    
                    print(f"[{Fore.GREEN}✓{Style.RESET_ALL}]")
                    self.goto_success_count[account_id] = self.goto_success_count.get(account_id, 0) + 1
                    return True
                    
                except asyncio.TimeoutError:
                    print(f"[{Fore.YELLOW}⏱️{Style.RESET_ALL}]")
                    self.timeout_errors_count[account_id] = self.timeout_errors_count.get(account_id, 0) + 1
                    
                    if wait_idx < len(wait_modes) - 1:
                        continue
                    break
                    
                except Exception as e:
                    error_msg = str(e)[:80]
                    print(f"[{Fore.RED}✗{Style.RESET_ALL}]")
                    
                    if "ERR_PROXY" in error_msg or "proxy" in error_msg.lower():
                        self.proxy_errors_count[account_id] = self.proxy_errors_count.get(account_id, 0) + 1
                        return False  # Не ретраить при прокси ошибке
                    
                    if wait_idx < len(wait_modes) - 1:
                        continue
                    break
            
            if retry_attempt < self.PAGE_GOTO_RETRIES:
                backoff = min(2 ** retry_attempt, 8) + random.uniform(0, 1)
                await asyncio.sleep(backoff)
        
        print(f"      {Fore.RED}❌ Не удалось загрузить {url[:60]}{Style.RESET_ALL}")
        self.goto_failure_count[account_id] = self.goto_failure_count.get(account_id, 0) + 1
        return False

    def get_page(self, account_id: str) -> Optional[Page]:
        return self._pages.get(account_id)

    def get_fingerprint(self, account_id: str) -> Optional[Fingerprint]:
        return self.fingerprint_store.get(account_id)

    async def close(self, account_id: str):
        """Закрыть браузер с сохранением cookies"""
        try:
            context = self._contexts.get(account_id)
            if context:
                try:
                    cookies = await context.cookies()
                    self._save_cookies(account_id, cookies)
                    print(f"  {Fore.GREEN}✅ Cookies сохранены ({len(cookies)} шт){Style.RESET_ALL}")
                    self.logger.action(account_id, "SAVE_COOKIES", "SUCCESS", count=len(cookies))
                except Exception as e:
                    self.logger.warning(account_id, f"Cookie save failed: {e}")

            page = self._pages.pop(account_id, None)
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            
            if context:
                try:
                    await context.close()
                except Exception:
                    pass
                    
            self._contexts.pop(account_id, None)
            print(f"  {Fore.CYAN}✅ Браузер закрыт{Style.RESET_ALL}")
            
        except Exception as e:
            self.logger.error(account_id, f"Error closing browser: {e}")

    async def close_all(self):
        """Закрыть все браузеры"""
        print(f"\n{Fore.CYAN}🛑 Закрываю все браузеры...{Style.RESET_ALL}")
        
        for acc_id in list(self._pages.keys()):
            try:
                await self.close(acc_id)
            except Exception:
                pass

        try:
            if self._browser:
                await self._browser.close()
                self._browser = None
        except Exception:
            pass

        try:
            if self._pw:
                await self._pw.stop()
                self._pw = None
        except Exception:
            pass

        self.logger.system("All browsers closed")

    async def reset_session(self, account_id: str):
        """Полный сброс сессии"""
        try:
            await self.close(account_id)
            
            cookies_file = self.cookies_dir / f"{account_id}.json"
            if cookies_file.exists():
                cookies_file.unlink()
            
            from core.browser.fingerprint import generate_fingerprint
            new_fp = generate_fingerprint(account_id)
            self.fingerprint_store._store[account_id] = new_fp
            
            print(f"  {Fore.YELLOW}🔄 Сессия сброшена{Style.RESET_ALL}")
            self.logger.success(account_id, "Session reset")
        except Exception as e:
            self.logger.error(account_id, f"Error resetting session: {e}")

    def _save_cookies(self, account_id: str, cookies: list):
        """Сохранить cookies"""
        try:
            cookies_file = self.cookies_dir / f"{account_id}.json"
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
        except Exception as e:
            self.logger.warning(account_id, f"Error saving cookies: {e}")

    def _load_cookies(self, account_id: str) -> list:
        """Загрузить cookies"""
        try:
            cookies_file = self.cookies_dir / f"{account_id}.json"
            if cookies_file.exists():
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(account_id, f"Error loading cookies: {e}")
        return []

    def get_diagnostics(self, account_id: str) -> Dict:
        """Получить диагностику"""
        return {
            "successful_launches": self.successful_launches.get(account_id, 0),
            "proxy_errors": self.proxy_errors_count.get(account_id, 0),
            "timeout_errors": self.timeout_errors_count.get(account_id, 0),
            "goto_success": self.goto_success_count.get(account_id, 0),
            "goto_failures": self.goto_failure_count.get(account_id, 0),
            "browser_crashes": self.browser_crash_count,
        }