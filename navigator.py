"""
🚀 NAVIGATOR v2.4 ADVANCED
✅ Улучшения:
- Добавлен метод perform_search для поиска по различным критериям
- Поддержка поиска по мототехнике, бюджету, объёму двигателя
- Интеграция с категориями Avito
"""

import asyncio
import random
from typing import Optional

from playwright.async_api import Page

from core.avito.detector import check_threats, ThreatType, ThreatInfo
from core.avito.selectors import AvitoUrls


class AvitoNavigator:
    """🚀 Навигатор по Avito с поддержкой поиска"""
    
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
        """Перейти на Avito с проверкой загрузки"""
        
        for attempt in range(1, attempts + 1):
            try:
                self.logger.info(account_id, f"🌐 [{attempt}/{attempts}] {url[:60]}")
                
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                
                await asyncio.sleep(2)
                
                is_ok = await self._verify_page_loaded(page, account_id, url)
                
                if is_ok:
                    threat = await check_threats(page)
                    
                    if threat and not threat.is_safe:
                        self.logger.risk(
                            account_id,
                            threat.type.value.upper(),
                            threat.message,
                            score=50
                        )
                    
                    self.logger.success(account_id, f"✅ Загружена ({attempt})")
                    return threat
                
                if attempt < attempts:
                    delay = random.uniform(2, 5)
                    self.logger.info(account_id, f"⏳ Ожидаю {delay:.1f} сек...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(account_id, f"❌ Не удалось загрузить после {attempts} попыток", severity="HIGH")
                    return None
            
            except asyncio.TimeoutError:
                self.logger.warning(account_id, f"⏱️ TIMEOUT (попытка {attempt}/{attempts})")
                
                if attempt < attempts:
                    await asyncio.sleep(random.uniform(3, 6))
                else:
                    return None
            
            except Exception as e:
                self.logger.error(account_id, f"goto error: {str(e)[:100]}", severity="MEDIUM")
                
                if attempt < attempts:
                    await asyncio.sleep(random.uniform(2, 5))
                else:
                    return None
        
        return None

    async def _verify_page_loaded(self, page: Page, account_id: str, url: str) -> bool:
        """Проверить что страница загружена"""
        
        try:
            current_url = page.url
            page_content = await page.content()
            
            if "avito" not in current_url.lower():
                self.logger.warning(account_id, f"⚠️ Не Avito: {current_url}")
                return False
            
            if len(page_content) < 1000:
                self.logger.warning(account_id, f"⚠️ Мало контента ({len(page_content)} символов)")
                return False
            
            if "html" not in page_content.lower():
                self.logger.warning(account_id, "⚠️ Нет HTML")
                return False
            
            self.logger.success(account_id, f"✅ Контент: {len(page_content)} символов")
            return True
        
        except Exception as e:
            self.logger.warning(account_id, f"⚠️ Ошибка проверки: {str(e)[:80]}")
            return False

    async def is_logged_in(self, page: Page) -> bool:
        """Проверить авторизацию"""
        try:
            if "login" in page.url.lower():
                return False
            
            profile_selectors = [
                '[data-marker="header/profile"]',
                'a[href*="/profile"]',
                '[data-marker="user-profile-button"]',
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
        """Кликнуть на объявление"""
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

    async def perform_search(
        self,
        page: Page,
        query: str,
        category: str = "all",
        account_id: str = "system",
    ) -> bool:
        """
        Выполнить поиск на Avito
        
        Args:
            page: Playwright Page
            query: Поисковый запрос
            category: Категория (all, mototehnika, auto и т.д.)
            account_id: ID аккаунта для логирования
            
        Returns:
            True если поиск успешен
        """
        try:
            # ─── ПЕРЕХОДИМ НА ПРАВИЛЬНУЮ КАТЕГОРИЮ (если нужно) ───
            if category == "mototehnika":
                category_url = "https://www.avito.ru/moskva/mototsikly_i_mototehnika"
                await self.goto(page, category_url, account_id)
                await asyncio.sleep(random.uniform(1, 2))
            
            # ─── ИЩЕМ ПОЛЕ ПОИСКА ───
            search_input = page.locator('input[data-marker="search-form/suggest"], input[placeholder*="Поиск"]').first
            
            if not await search_input.is_visible(timeout=2000):
                self.logger.warning(account_id, f"Поле поиска не найдено")
                return False
            
            # ─── КЛИКАЕМ НА ПОЛЕ ПОИСКА ───
            await search_input.click()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # ─── ПЕЧАТАЕМ ЗАПРОС ───
            await search_input.type(query, delay=random.uniform(30, 80))
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
            # ─── НАЖИМАЕМ ENTER ИЛИ КЛИКАЕМ КНОПКУ ПОИСКА ───
            submit_button = page.locator('button[data-marker="search-form/submit"], button[type="submit"]').first
            
            if await submit_button.is_visible(timeout=1000):
                await submit_button.click()
            else:
                await search_input.press("Enter")
            
            # ─── ЖДЁМ ЗАГРУЗКИ РЕЗУЛЬТАТОВ ───
            await asyncio.sleep(random.uniform(2, 4))
            
            # ─── ПРОВЕРЯЕМ ЧТО РЕЗУЛЬТАТЫ ЗАГРУЖЕНЫ ───
            listings_count = await page.locator('[data-marker="item"]').count()
            
            if listings_count > 0:
                self.logger.success(account_id, f"✅ Поиск '{query}' — найдено {listings_count} объявлений")
                return True
            else:
                self.logger.warning(account_id, f"⚠️ Поиск '{query}' — результатов не найдено")
                return False
            
        except Exception as e:
            self.logger.error(account_id, f"Search error: {str(e)[:100]}", severity="MEDIUM")
            return False

    async def search(self, page: Page, query: str) -> bool:
        """Поиск (legacy метод)"""
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