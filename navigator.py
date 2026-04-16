# core/avito/navigator.py
"""
🚀 NAVIGATOR — Навигация по Avito с полной защитой
"""

import asyncio
from typing import Optional

from playwright.async_api import Page

from core.avito.detector import check_threats, ThreatType, ThreatInfo
from core.avito.selectors import AvitoUrls


class AvitoNavigator:
    def __init__(self, logger):
        self.logger = logger

    async def goto(
        self,
        page: Page,
        url: str,
        account_id: str = "system",
        attempts: int = 3,
        timeout_ms: int = 30000,
    ) -> Optional[ThreatInfo]:
        """Перейти на страницу с проверкой угроз"""
        for attempt in range(1, attempts + 1):
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                await asyncio.sleep(1.0)
                
                # Проверяем угрозы
                threat = await check_threats(page)
                
                if threat and not threat.is_safe:
                    self.logger.risk(
                        account_id,
                        threat.type.value.upper(),
                        threat.message,
                        score=50
                    )
                    
                    if threat.type == ThreatType.BAN:
                        self.logger.error(account_id, "БАН АККАУНТА", severity="CRITICAL")
                    elif threat.type == ThreatType.BLOCK:
                        self.logger.error(account_id, "БЛОКИ��ОВКА IP", severity="CRITICAL")
                    elif threat.type == ThreatType.CAPTCHA:
                        self.logger.warning(account_id, "Требуется капча")
                
                return threat
                
            except Exception as e:
                if attempt < attempts:
                    await asyncio.sleep(2.0)
                    continue
                else:
                    self.logger.error(account_id, f"goto error: {e}")
                    return None
        
        return None

    async def is_logged_in(self, page: Page) -> bool:
        """Проверить авторизацию"""
        try:
            # Если URL содержит login - не авторизирован
            if "login" in page.url.lower():
                return False
            
            # Проверяем наличие кнопок профиля
            profile_selectors = [
                '[data-marker="header/profile"]',
                'a[href*="/profile"]',
            ]
            
            for selector in profile_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        return True
                except Exception:
                    pass
            
            return False
        except Exception:
            return False

    async def click_listing(self, page: Page, index: int = 0) -> bool:
        """Кликнуть на объявление по индексу"""
        try:
            listings = await page.locator('[data-marker="item"]').all()
            
            if index >= len(listings):
                return False
            
            listing = listings[index]
            await listing.click()
            await asyncio.sleep(2.0)
            
            return True
        except Exception:
            return False

    async def search(self, page: Page, query: str) -> bool:
        """Поиск"""
        try:
            search_input = page.locator('input[data-marker="search-form/suggest"]').first
            
            if not await search_input.is_visible():
                return False
            
            await search_input.click()
            await asyncio.sleep(0.5)
            await search_input.type(query)
            await asyncio.sleep(1.0)
            
            submit_button = page.locator('button[data-marker="search-form/submit"]').first
            await submit_button.click()
            
            await asyncio.sleep(3.0)
            return True
        except Exception:
            return False

    async def go_back(self, page: Page) -> bool:
        """Назад"""
        try:
            await page.go_back()
            await asyncio.sleep(1.5)
            return True
        except Exception:
            return False