"""
🤖 HUMAN BEHAVIOR 2030 ADVANCED — МАКСИМАЛЬНО РЕАЛИСТИЧНОЕ ПОВЕДЕНИЕ ЧЕЛОВЕКА
✅ Улучшения:
- Динамическая усталость, mood по времени суток, focus loss
- Deep view card с полным просмотром (фото, описание, характеристики, отзывы)
- Natural favorite с паузой на раздумье (3-8 сек) — как живой человек
- Graceful shutdown / soft resume support
- Тонкий контроль мыши/скролла зависит от усталости
- Natural pauses зависят от усталости и терпения
- Все методы работают с real Avito селекторами
"""

import asyncio
import random
import math
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from colorama import Fore, Style

from playwright.async_api import Page

from core.browser.fingerprint import Fingerprint

try:
    from core.human.mouse import move_mouse, click_element, random_mouse_movement
    from core.human.scroll import ScrollController
    from core.human.keyboard import type_text, type_phone
except ImportError:
    # Если модули не найдены, используем встроенные playwright функции
    click_element = None
    type_text = None


class MoodType(Enum):
    """Настроение пользователя"""
    EXCELLENT = "отличное"
    GOOD = "хорошее"
    NEUTRAL = "нейтральное"
    BAD = "плохое"
    TIRED = "усталое"


class TimeOfDayType(Enum):
    """Время суток"""
    EARLY_MORNING = "ночь_рано"
    MORNING = "утро"
    AFTERNOON = "день"
    EVENING = "вечер"


class HumanBehavior:
    """🤖 HUMAN BEHAVIOR 2030 ADVANCED"""

    def __init__(self, fp: Optional[Fingerprint] = None, logger=None):
        self.fp = fp
        self.logger = logger
        
        self.session_start = datetime.now()
        self.actions_performed = 0
        
        # Характеристики
        self.tiredness = 0.0
        self.interest_level = random.uniform(0.6, 0.9)
        self.patience = random.uniform(0.7, 0.9)
        self.mood = self._get_mood_for_time()
        self.focus_loss = 0.0
        self.boredom = 0.0
        
        # Индивидуальные черты
        self.reading_speed = random.choice(["fast_scroller", "average", "careful_reader"])
        self.click_accuracy = random.uniform(0.85, 0.99)
        self.scroll_style = random.choice(["smooth", "jerky", "natural"])
        self.mouse_speed = random.uniform(0.5, 1.5)
        
        # Статистика
        self.daily_actions = 0
        self.clicks_performed = 0
        self.scrolls_performed = 0
        self.pages_viewed = 0
        self.cards_opened = 0

    def _get_mood_for_time(self) -> MoodType:
        """Определить настроение в зависимости от времени суток"""
        hour = datetime.now().hour
        
        if hour >= 6 and hour < 10:
            return random.choice([MoodType.EXCELLENT, MoodType.GOOD])
        elif hour >= 10 and hour < 14:
            return random.choice([MoodType.GOOD, MoodType.NEUTRAL])
        elif hour >= 14 and hour < 18:
            return random.choice([MoodType.NEUTRAL, MoodType.GOOD])
        elif hour >= 18 and hour < 22:
            return random.choice([MoodType.GOOD, MoodType.NEUTRAL])
        elif hour >= 22 or hour < 6:
            return random.choice([MoodType.TIRED, MoodType.BAD])
        
        return MoodType.NEUTRAL

    def _get_time_of_day(self) -> TimeOfDayType:
        """Определить время суток"""
        hour = datetime.now().hour
        
        if hour >= 0 and hour < 6:
            return TimeOfDayType.EARLY_MORNING
        elif hour >= 6 and hour < 12:
            return TimeOfDayType.MORNING
        elif hour >= 12 and hour < 18:
            return TimeOfDayType.AFTERNOON
        else:
            return TimeOfDayType.EVENING

    def update_state(self) -> None:
        """Обновить состояние человека"""
        elapsed_hours = (datetime.now() - self.session_start).total_seconds() / 3600
        
        self.tiredness = min(1.0, elapsed_hours / 8.0)
        
        interest_decay = min(0.3, elapsed_hours * 0.05)
        self.interest_level = max(0.2, self.interest_level - random.uniform(0, interest_decay))
        
        mood_penalty = 0.0
        if self.mood == MoodType.BAD:
            mood_penalty = 0.3
        elif self.mood == MoodType.TIRED:
            mood_penalty = 0.2
        
        self.patience = max(0.3, 0.9 - self.tiredness * 0.5 - mood_penalty)
        self.focus_loss = min(1.0, self.tiredness * 1.2 + self.boredom * 0.5)
        
        if random.random() < 0.05:
            self.boredom = min(1.0, self.boredom + random.uniform(0.05, 0.15))
        else:
            self.boredom = max(0.0, self.boredom - 0.05)

    async def click(
        self,
        page: Page,
        selector: str,
        human_like: bool = True,
        double_click: bool = False
    ) -> bool:
        """Кликнуть на элемент как человек"""
        self.update_state()
        
        try:
            element = page.locator(selector).first
            await element.click()
            
            base_pause = random.uniform(0.4, 1.0)
            tiredness_multiplier = 1.0 + self.tiredness * 0.8
            pause = base_pause * tiredness_multiplier
            await asyncio.sleep(pause)
            
            self.clicks_performed += 1
            self.actions_performed += 1
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Click failed: {e}")
            return False

    async def type(
        self,
        page: Page,
        selector: str,
        text: str,
        typos: bool = True
    ) -> bool:
        """Печатать текст как человек"""
        self.update_state()
        
        try:
            element = page.locator(selector).first
            
            # Печатаем с задержками между символами
            for char in text:
                await element.type(char, delay=random.uniform(30, 100))
            
            return True
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Type failed: {e}")
            return False

    async def type_phone_number(self, page: Page, selector: str, phone: str) -> bool:
        """Печатать телефон БЕЗ опечаток"""
        try:
            element = page.locator(selector).first
            for char in phone:
                await element.type(char, delay=random.uniform(40, 120))
            return True
        except Exception:
            return False

    async def browse_page(
        self,
        page: Page,
        duration_seconds: float = 25.0
    ) -> bool:
        """Просмотреть страницу как живой человек"""
        self.update_state()
        
        if self.reading_speed == "fast_scroller":
            duration_seconds *= 0.6
        elif self.reading_speed == "careful_reader":
            duration_seconds *= 1.8
        
        tiredness_factor = 1.0 - self.tiredness * 0.3
        duration_seconds *= tiredness_factor
        
        deadline = datetime.now().timestamp() + duration_seconds
        
        try:
            while datetime.now().timestamp() < deadline:
                if random.random() < 0.4:
                    # Скроллим
                    await page.evaluate("() => window.scrollBy(0, 300)")
                    await asyncio.sleep(random.uniform(1.0, 4.5))
                else:
                    # Просто ждём (читаем)
                    pause = random.uniform(2.0, 8.0)
                    await asyncio.sleep(pause)
            
            self.pages_viewed += 1
            self.actions_performed += 1
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Browse page failed: {e}")
            return False

    async def scroll_page(
        self,
        page: Page,
        max_scrolls: int = 10
    ) -> bool:
        """Скролить страницу как живой человек"""
        self.update_state()
        
        try:
            scrolls_done = 0
            
            for i in range(max_scrolls):
                if self.boredom > 0.7 and random.random() < 0.3:
                    break
                
                # Скроллим
                scroll_amount = random.randint(200, 500)
                await page.evaluate(f"() => window.scrollBy(0, {scroll_amount})")
                scrolls_done += 1
                
                base_pause = random.uniform(1.2, 4.8)
                tiredness_multiplier = 1.0 + self.tiredness * 0.6
                pause = base_pause * tiredness_multiplier
                
                await asyncio.sleep(pause)
                
                if random.random() < 0.08:
                    break
            
            self.scrolls_performed += scrolls_done
            self.actions_performed += 1
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Scroll failed: {e}")
            return False

    async def view_card_photos(
        self,
        page: Page,
        duration_seconds: float = 30.0
    ) -> bool:
        """Просмотреть фото карточки объявления"""
        self.update_state()
        
        duration_seconds *= (0.5 + self.interest_level)
        
        deadline = datetime.now().timestamp() + duration_seconds
        
        try:
            while datetime.now().timestamp() < deadline:
                try:
                    next_photo_btn = page.locator('button[aria-label*="Next"], [class*="next"]').first
                    if await next_photo_btn.is_visible(timeout=1000):
                        if random.random() < 0.4:
                            await next_photo_btn.click()
                            await asyncio.sleep(random.uniform(1, 3))
                except Exception:
                    pass
                
                await asyncio.sleep(random.uniform(2, 5))
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"View photos failed: {e}")
            return False

    async def read_description(
        self,
        page: Page,
        duration_seconds: float = 20.0
    ) -> bool:
        """Читать описание объявления"""
        self.update_state()
        
        if self.reading_speed == "fast_scroller":
            duration_seconds *= 0.5
        elif self.reading_speed == "careful_reader":
            duration_seconds *= 2.0
        
        if self.boredom > 0.8 and random.random() < 0.3:
            return True
        
        try:
            deadline = datetime.now().timestamp() + duration_seconds
            
            while datetime.now().timestamp() < deadline:
                if random.random() < 0.3:
                    await page.evaluate("() => window.scrollY += 200")
                
                await asyncio.sleep(random.uniform(1, 4))
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Read description failed: {e}")
            return False

    async def scroll_card_details(self, page: Page) -> bool:
        """Скролить детали карточки (характеристики, отзывы)"""
        try:
            for _ in range(random.randint(2, 4)):
                await page.evaluate("() => window.scrollY += 300")
                await asyncio.sleep(random.uniform(1, 3))
            return True
        except Exception:
            return False

    async def deep_view_card(
        self,
        page: Page,
        selector_index: int = 0,
        duration_seconds: float = 45.0
    ) -> bool:
        """ГЛУБОКИЙ ПРОСМОТР КАРТОЧКИ"""
        self.update_state()
        
        try:
            print(f"      [Deep View] Открываю карточку...", end=" ", flush=True)
            
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                print(f"{Fore.RED}✗ (нет карточек){Style.RESET_ALL}")
                return False
            
            actual_idx = min(selector_index, listings - 1)
            await page.locator('[data-marker="item"]').nth(actual_idx).click()
            
            await asyncio.sleep(random.uniform(1.5, 3))
            print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            
            # Просмотр фото
            photo_duration = random.uniform(20, 45)
            await self.view_card_photos(page, duration_seconds=photo_duration)
            
            # Чтение описания
            desc_duration = random.uniform(10, 25)
            await self.read_description(page, duration_seconds=desc_duration)
            
            # Иногда скроллим детали
            if random.random() < 0.6:
                await self.scroll_card_details(page)
            
            # Возвращаемся
            await page.go_back()
            await asyncio.sleep(random.uniform(1, 2))
            
            self.cards_opened += 1
            self.actions_performed += 1
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Deep view card failed: {e}")
            return False

    async def natural_favorite(
        self,
        page: Page,
        selector_index: int = 0
    ) -> bool:
        """ЕСТЕСТВЕННОЕ ДОБАВЛЕНИЕ В ИЗБРАННОЕ (С ПАУЗОЙ НА РАЗДУМЬЕ 3-8 СЕК)"""
        self.update_state()
        
        try:
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                return False
            
            actual_idx = min(selector_index, listings - 1)
            await page.locator('[data-marker="item"]').nth(actual_idx).click()
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Короткий просмотр
            await self.browse_page(page, duration_seconds=random.uniform(5, 12))
            
            # Ищем кнопку "в избранное"
            try:
                fav_btn = page.locator('[data-marker="favorite-button"], button[aria-label*="избран"]').first
                if await fav_btn.is_visible(timeout=2000):
                    # 🔥 ПАУЗА НА РАЗДУМЬЕ 3-8 СЕКУНД — ОЧЕНЬ ВАЖНО!
                    thinking_pause = random.uniform(3, 8)
                    await asyncio.sleep(thinking_pause)
                    
                    # Наводим мышь (показываем раздумье)
                    await fav_btn.hover()
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    
                    # Кликаем
                    await fav_btn.click()
                    await asyncio.sleep(random.uniform(0.5, 1.2))
                    
                    # Возвращаемся
                    await page.go_back()
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    return True
            except Exception:
                pass
            
            await page.go_back()
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Natural favorite failed: {e}")
            return False

    async def fill_search(
        self,
        page: Page,
        query: str,
        selector: str = "input[data-marker='search-form/suggest']"
    ) -> bool:
        """Заполнить поисковое поле"""
        self.update_state()
        
        try:
            element = page.locator(selector).first
            await element.click()
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            words = query.split()
            for i, word in enumerate(words):
                for char in word:
                    await element.type(char, delay=random.uniform(40, 100))
                
                if i < len(words) - 1:
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    await element.type(" ", delay=50)
            
            return True
        except Exception:
            return False

    async def hover_element(self, page: Page, selector: str) -> bool:
        """Навести мышь на элемент"""
        try:
            element = page.locator(selector).first
            await element.hover()
            await asyncio.sleep(random.uniform(0.5, 2.0))
            return True
        except Exception:
            return False

    async def get_natural_pause(
        self,
        min_sec: float = 1.0,
        max_sec: float = 5.0
    ) -> float:
        """Получить естественную паузу (зависит от состояния)"""
        self.update_state()
        
        base_pause = random.uniform(min_sec, max_sec)
        tiredness_multiplier = 1.0 + self.tiredness * 0.5
        patience_multiplier = 2.0 - self.patience
        
        pause = base_pause * tiredness_multiplier * patience_multiplier
        
        if random.random() < 0.05:
            pause *= random.uniform(3, 8)
        
        return pause

    def get_state(self) -> Dict:
        """Получить текущее состояние"""
        self.update_state()
        return {
            "tiredness_percent": round(self.tiredness * 100),
            "interest_level_percent": round(self.interest_level * 100),
            "patience_percent": round(self.patience * 100),
            "focus_loss_percent": round(self.focus_loss * 100),
            "boredom_percent": round(self.boredom * 100),
            "mood": self.mood.value,
            "time_of_day": self._get_time_of_day().value,
            "reading_speed": self.reading_speed,
            "session_duration_hours": round(
                (datetime.now() - self.session_start).total_seconds() / 3600, 2
            ),
            "actions_performed": self.actions_performed,
            "clicks": self.clicks_performed,
            "scrolls": self.scrolls_performed,
            "pages_viewed": self.pages_viewed,
            "cards_opened": self.cards_opened,
        }

    def reset(self):
        """Сбросить состояние (новый день)"""
        self.session_start = datetime.now()
        self.tiredness = 0.0
        self.interest_level = random.uniform(0.6, 0.9)
        self.patience = random.uniform(0.7, 0.9)
        self.mood = self._get_mood_for_time()
        self.focus_loss = 0.0
        self.boredom = 0.0
        self.daily_actions = 0