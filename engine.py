# core/warmup/engine.py
"""
🔥 WARMUP ENGINE 2030 ADVANCED — ПОЛНЫЙ ПРОГРЕВ ТОЛЬКО МОТОТЕХНИКИ
✅ ИСПРАВЛЕНИЯ:
- Все 5 фаз работают ТОЛЬКО с мототехникой (питбайки, квадроциклы, мотоциклы)
- Deep views обязательны в каждой фазе (открытие карточек + просмотр фото/описания)
- Natural favorite добавляетс�� в 30-50% случаев
- Паузы динамические и естественные
- Удалён triple_click (заменён fill)
- Улучшена загрузка Avito (networkidle вместо domcontentloaded)
"""

import asyncio
import random
from datetime import datetime
from typing import Optional
from colorama import Fore, Style

from playwright.async_api import Page

from core.avito.navigator import AvitoNavigator
from core.avito.selectors import AvitoUrls, AvitoSelectors
from core.avito.detector import ThreatType
from core.human.behavior import HumanBehavior
from core.safety.night_mode import NightMode
from core.browser.fingerprint import Fingerprint


class WarmupEngine:
    """Полный прогрев аккаунта ТОЛЬКО МОТОТЕХНИКА"""

    def __init__(self, logger, executor=None, notifier=None):
        self.logger = logger
        self.executor = executor
        self.notifier = notifier
        self.total_warmup_duration = 0.0
        self.deep_views_count = 0

    async def run_full_warmup(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ) -> bool:
        """Запустить полный прогрев из 5 фаз МОТОТЕХНИКИ"""
        
        warmup_start = datetime.now()
        
        print(f"\n{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🔥 ПОЛНЫЙ ПРОГРЕВ АККАУНТА: 5 ФАЗ МОТОТЕХНИКИ (75-105 МИНУТ)':^90}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}\n")

        phases = [
            ("Фаза 1: Введение в мототехнику (категория + листание)", self._phase_1_intro_moto),
            ("Фаза 2: Питбайки 40-60к (поиск + deep views)", self._phase_2_pitbikes),
            ("Фаза 3: Квадроциклы и мотоциклы (категория + карточки)", self._phase_3_quads_motos),
            ("Фаза 4: Эндуро и кросс (поиск + детальный просмотр)", self._phase_4_enduro_cross),
            ("Фаза 5: Запчасти и аксессуары мото (категория + добавление в избранное)", self._phase_5_parts),
        ]

        completed_phases = 0
        self.deep_views_count = 0

        for phase_num, (phase_name, phase_func) in enumerate(phases, 1):
            # Проверяем ночной режим перед каждой фазой
            if not night_mode.can_work(account_id):
                print(f"\n  {Fore.BLUE}🌙 Ночной режим активен — прогрев приостановлен на фазе {phase_num}{Style.RESET_ALL}")
                self.logger.warning(account_id, f"Warmup paused by night mode at phase {phase_num}")
                break

            print(f"\n{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}[ФАЗА {phase_num}/5] {phase_name}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n")

            try:
                # Запускаем фазу с timeout 20 минут
                success = await asyncio.wait_for(
                    phase_func(page, account_id, navigator, fp, browser_launcher),
                    timeout=1200.0
                )

                if success:
                    print(f"\n  {Fore.GREEN}✅ Фаза {phase_num} завершена{Style.RESET_ALL}")
                    self.logger.success(account_id, f"Phase {phase_num} completed")
                    completed_phases += 1
                else:
                    print(f"\n  {Fore.YELLOW}⚠️ Фаза {phase_num} имела проблемы{Style.RESET_ALL}")
                    self.logger.warning(account_id, f"Phase {phase_num} had issues")
                    completed_phases += 1

                # Пауза между фазами (8-25 сек)
                pause = random.uniform(8.0, 25.0)
                print(f"  {Fore.CYAN}⏱️ Пауза {pause:.1f}сек перед фазой {phase_num + 1}...{Style.RESET_ALL}")
                await asyncio.sleep(pause)

            except asyncio.TimeoutError:
                print(f"  {Fore.RED}❌ Timeout в Фазе {phase_num} (>20 мин){Style.RESET_ALL}")
                self.logger.error(account_id, f"Phase {phase_num} timeout", severity="HIGH")
                continue

            except Exception as e:
                print(f"  {Fore.RED}❌ Ошибка в Фазе {phase_num}: {str(e)[:100]}{Style.RESET_ALL}")
                self.logger.error(account_id, f"Error in phase {phase_num}: {e}", severity="HIGH")
                continue

        self.total_warmup_duration = (datetime.now() - warmup_start).total_seconds()

        print(f"\n{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'✅ ПРОГРЕВ ЗАВЕРШЁН!':^90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{f'Завершено фаз: {completed_phases}/5 | Deep views: {self.deep_views_count} | Время: {self.total_warmup_duration/60:.1f} мин':^90}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}\n")

        self.logger.action(account_id, "WARMUP_COMPLETE", "SUCCESS", 
                          phases_completed=completed_phases, 
                          deep_views=self.deep_views_count,
                          duration_minutes=self.total_warmup_duration/60)
        
        # Прогрев считается успешным если прошли минимум 4 фазы
        return completed_phases >= 4

    async def _phase_1_intro_moto(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ) -> bool:
        """
        ФАЗА 1: Введение в мототехнику
        - Переход в категорию "Мототехника"
        - Листание объявлений (3-5 скроллов)
        - Deep view 2-3 карточек
        """
        human = HumanBehavior(fp, self.logger)
        
        try:
            print("    🔍 Переход в категорию 'Мототехника'...", end=" ", flush=True)
            
            # Переходим в катег��рию мототехники
            url = "https://www.avito.ru/moskva/mototsikly_i_mototehnika"
            try:
                await asyncio.wait_for(
                    page.goto(url, wait_until="networkidle", timeout=25000),
                    timeout=30.0
                )
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️ (перезагрузка){Style.RESET_ALL}")
                await asyncio.wait_for(
                    page.goto(url, wait_until="domcontentloaded", timeout=20000),
                    timeout=25.0
                )
            
            # Просмотр страницы 20-30 сек
            await human.browse_page(page, duration_seconds=random.uniform(20, 30))
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Скролл объявлений 3-5 раз
            scrolls = random.randint(3, 5)
            print(f"    📜 Листание {scrolls} раз...")
            for i in range(scrolls):
                await human.scroll_page(page, max_scrolls=1)
                await asyncio.sleep(random.uniform(2.0, 5.0))
            
            # Deep view 2-3 карточек
            deep_views_target = random.randint(2, 3)
            print(f"    🔎 Deep view {deep_views_target} карточек...")
            for idx in range(deep_views_target):
                success = await human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(45, 75))
                if success:
                    self.deep_views_count += 1
                await asyncio.sleep(random.uniform(1.5, 3.0))
            
            return True
            
        except Exception as e:
            self.logger.warning(account_id, f"Phase 1 error: {e}")
            return False

    async def _phase_2_pitbikes(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ) -> bool:
        """
        ФАЗА 2: Питбайки 40-60 тысяч рублей
        - Поиск "питбайк" или "питбайки 40000" / "питбайки 50000" / "питбайки 60000"
        - Просмотр 20-35 сек
        - Deep view 3-4 карточек
        - Иногда добавление в избранное (20%)
        """
        human = HumanBehavior(fp, self.logger)
        
        try:
            # Переходим в категорию мототехники
            url = "https://www.avito.ru/moskva/mototsikly_i_mototehnika"
            print("    🔍 Переход в мототехнику для поиска питбайков...", end=" ", flush=True)
            try:
                await asyncio.wait_for(
                    page.goto(url, wait_until="networkidle", timeout=25000),
                    timeout=30.0
                )
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
            
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # Выбираем поисковый запрос
            search_queries = [
                "питбайк",
                "питбайки 40000",
                "питбайки 50000", 
                "питбайки 60000",
            ]
            query = random.choice(search_queries)
            
            print(f"    🔎 Поиск: '{query}'...", end=" ", flush=True)
            
            # Ищем поле поиска
            search_input = page.locator('input[data-marker="search-form/suggest"]').first
            if await search_input.is_visible(timeout=3000):
                await search_input.click()
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                # Очищаем поле
                try:
                    await search_input.fill("")
                except Exception:
                    pass
                
                # Печатаем запрос
                await human.type(page, 'input[data-marker="search-form/suggest"]', query, typos=True)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Кликаем кнопку поиска
                submit_btn = page.locator('button[data-marker="search-form/submit"]').first
                if await submit_btn.is_visible(timeout=2000):
                    await submit_btn.click()
                    print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                    
                    # Ждём загрузки результатов
                    try:
                        await asyncio.wait_for(
                            page.wait_for_load_state("networkidle", timeout=25000),
                            timeout=30.0
                        )
                    except Exception:
                        await asyncio.sleep(3.0)
                else:
                    return False
            else:
                return False
            
            # Просмотр результатов 20-35 сек
            await human.browse_page(page, duration_seconds=random.uniform(20, 35))
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Deep view 3-4 карточек
            deep_views_target = random.randint(3, 4)
            print(f"    🔎 Deep view {deep_views_target} питбайков...")
            for idx in range(deep_views_target):
                success = await human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(50, 90))
                if success:
                    self.deep_views_count += 1
                    
                    # Иногда добавляем в избранное (20%)
                    if random.random() < 0.2:
                        try:
                            fav_btn = page.locator('[data-marker="favorite-button"]').first
                            if await fav_btn.is_visible(timeout=2000):
                                await asyncio.sleep(random.uniform(0.8, 2.0))
                                await fav_btn.click()
                                print(f"      ⭐ Добавлено в избранное")
                                await asyncio.sleep(random.uniform(0.5, 1.5))
                        except Exception:
                            pass
                
                await asyncio.sleep(random.uniform(1.5, 3.0))
            
            return True
            
        except Exception as e:
            self.logger.warning(account_id, f"Phase 2 error: {e}")
            return False

    async def _phase_3_quads_motos(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ) -> bool:
        """
        ФАЗА 3: Квадроциклы и мотоциклы
        - Переход в категорию "Мототехника"
        - Листание 3-4 раза
        - Deep view 3-4 карточек
        """
        human = HumanBehavior(fp, self.logger)
        
        try:
            print("    🔍 Категория 'Мототехника' (основной вид)...", end=" ", flush=True)
            
            url = "https://www.avito.ru/moskva/mototsikly_i_mototehnika"
            try:
                await asyncio.wait_for(
                    page.goto(url, wait_until="networkidle", timeout=25000),
                    timeout=30.0
                )
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
            
            # Просмотр 25-40 сек
            await human.browse_page(page, duration_seconds=random.uniform(25, 40))
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Листание 3-4 раза
            scrolls = random.randint(3, 4)
            print(f"    📜 Листание {scrolls} раз...")
            for i in range(scrolls):
                await human.scroll_page(page, max_scrolls=1)
                await asyncio.sleep(random.uniform(2.0, 5.0))
            
            # Deep view 3-4 карточек
            deep_views_target = random.randint(3, 4)
            print(f"    🔎 Deep view {deep_views_target} карточек...")
            for idx in range(deep_views_target):
                success = await human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(50, 85))
                if success:
                    self.deep_views_count += 1
                await asyncio.sleep(random.uniform(1.5, 3.0))
            
            return True
            
        except Exception as e:
            self.logger.warning(account_id, f"Phase 3 error: {e}")
            return False

    async def _phase_4_enduro_cross(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ) -> bool:
        """
        ФАЗА 4: Эндуро и кросс
        - Поиск "эндуро" или "кросс"
        - Просмотр результатов
        - Deep view 2-3 карточек
        """
        human = HumanBehavior(fp, self.logger)
        
        try:
            url = "https://www.avito.ru/moskva/mototsikly_i_mototehnika"
            print("    🔍 Поиск эндуро/кросс...", end=" ", flush=True)
            
            try:
                await asyncio.wait_for(
                    page.goto(url, wait_until="networkidle", timeout=25000),
                    timeout=30.0
                )
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
            
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # Выбираем поисковый запрос
            search_queries = ["эндуро", "кросс", "мотоцикл эндуро", "кросс байк"]
            query = random.choice(search_queries)
            
            print(f"    🔎 Поиск: '{query}'...", end=" ", flush=True)
            
            search_input = page.locator('input[data-marker="search-form/suggest"]').first
            if await search_input.is_visible(timeout=3000):
                await search_input.click()
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                try:
                    await search_input.fill("")
                except Exception:
                    pass
                
                await human.type(page, 'input[data-marker="search-form/suggest"]', query, typos=True)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                submit_btn = page.locator('button[data-marker="search-form/submit"]').first
                if await submit_btn.is_visible(timeout=2000):
                    await submit_btn.click()
                    print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                    
                    try:
                        await asyncio.wait_for(
                            page.wait_for_load_state("networkidle", timeout=25000),
                            timeout=30.0
                        )
                    except Exception:
                        await asyncio.sleep(3.0)
                else:
                    return False
            else:
                return False
            
            # Просмотр 20-30 сек
            await human.browse_page(page, duration_seconds=random.uniform(20, 30))
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Deep view 2-3 карточек
            deep_views_target = random.randint(2, 3)
            print(f"    🔎 Deep view {deep_views_target} карточек...")
            for idx in range(deep_views_target):
                success = await human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(45, 75))
                if success:
                    self.deep_views_count += 1
                await asyncio.sleep(random.uniform(1.5, 3.0))
            
            return True
            
        except Exception as e:
            self.logger.warning(account_id, f"Phase 4 error: {e}")
            return False

    async def _phase_5_parts(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ) -> bool:
        """
        ФАЗА 5: Запчасти и аксессуары мото
        - Переход в "Запчасти и аксессуары"
        - Листание 2-3 раза
        - Deep view 2 карточек
        - Добавление в избранное 30-50%
        """
        human = HumanBehavior(fp, self.logger)
        
        try:
            print("    🔍 Категория 'Запчасти и аксессуары'...", end=" ", flush=True)
            
            url = "https://www.avito.ru/moskva/zapchasti_i_aksessuary"
            try:
                await asyncio.wait_for(
                    page.goto(url, wait_until="networkidle", timeout=25000),
                    timeout=30.0
                )
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
            
            # Просмотр 20-30 сек
            await human.browse_page(page, duration_seconds=random.uniform(20, 30))
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Листание 2-3 раза
            scrolls = random.randint(2, 3)
            print(f"    📜 Листание {scrolls} раз...")
            for i in range(scrolls):
                await human.scroll_page(page, max_scrolls=1)
                await asyncio.sleep(random.uniform(2.0, 5.0))
            
            # Deep view + добавление в избранное для 2 карточек
            print(f"    🔎 Deep view 2 карточек + добавление в избранное...")
            for idx in range(2):
                success = await human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(40, 70))
                if success:
                    self.deep_views_count += 1
                    
                    # Добавляем в избранное 30-50%
                    if random.random() < 0.4:
                        try:
                            fav_btn = page.locator('[data-marker="favorite-button"]').first
                            if await fav_btn.is_visible(timeout=2000):
                                await asyncio.sleep(random.uniform(0.8, 2.0))
                                await fav_btn.click()
                                print(f"      ⭐ Добавлено в избранное")
                                await asyncio.sleep(random.uniform(0.5, 1.5))
                        except Exception:
                            pass
                
                await asyncio.sleep(random.uniform(1.5, 3.0))
            
            return True
            
        except Exception as e:
            self.logger.warning(account_id, f"Phase 5 error: {e}")
            return False


class AliveMode:
    """Alive Mode - фоновая активность как реальный человек"""

    def __init__(self, logger, executor=None, notifier=None):
        self.logger = logger
        self.executor = executor
        self.notifier = notifier
        self.running = False
        self.iteration_count = 0

    async def run(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
        browser_launcher = None,
    ):
        """
        Запустить Alive Mode
        
        Поведение как у живого человека:
        - Просмотр разных категорий
        - Deep views карточек
        - Добавление в избранное
        - Поиск
        - Случайные паузы (10-60 минут)
        """
        self.running = True
        human = HumanBehavior(fp, self.logger)

        print(f"\n{Fore.GREEN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'✅ ALIVE MODE — БОТ АКТИВЕН 24/7':^90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'Просмотр карточек, добавление в избранное, поиск' :^90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 90}{Style.RESET_ALL}\n")

        self.logger.system(f"{account_id}: Alive Mode started")

        try:
            while self.running:
                # Проверяем ночной режим
                if not night_mode.can_work(account_id):
                    print(f"  {Fore.BLUE}🌙 Ночной режим — браузер закроется на 8+ часов{Style.RESET_ALL}")
                    await asyncio.sleep(300)
                    continue

                # Случайное действие
                action = random.choices(
                    ["deep_view_moto", "deep_view_other", "search", "browse", "favorites", "wait"],
                    weights=[0.35, 0.20, 0.15, 0.15, 0.10, 0.05],
                    k=1
                )[0]

                try:
                    if action == "deep_view_moto":
                        print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Deep view мототехники...{Style.RESET_ALL}")
                        try:
                            await asyncio.wait_for(
                                page.goto("https://www.avito.ru/moskva/mototsikly_i_mototehnika", wait_until="networkidle", timeout=25000),
                                timeout=30.0
                            )
                        except Exception:
                            pass
                        
                        # Deep view 1-2 карточек
                        for idx in range(random.randint(1, 2)):
                            try:
                                await asyncio.wait_for(
                                    human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(45, 90)),
                                    timeout=120.0
                                )
                                
                                # Может добавить в избранное
                                if random.random() < 0.3:
                                    try:
                                        fav = page.locator('[data-marker="favorite-button"]').first
                                        if await fav.is_visible(timeout=2000):
                                            await fav.click()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            
                            await asyncio.sleep(random.uniform(2.0, 5.0))

                    elif action == "deep_view_other":
                        categories = [
                            ("https://www.avito.ru/moskva/avtomobili", "Авто"),
                            ("https://www.avito.ru/moskva/kollektsii", "Коллекции"),
                        ]
                        url, cat_name = random.choice(categories)
                        
                        print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Deep view {cat_name}...{Style.RESET_ALL}")
                        try:
                            await asyncio.wait_for(
                                page.goto(url, wait_until="networkidle", timeout=25000),
                                timeout=30.0
                            )
                        except Exception:
                            pass
                        
                        for idx in range(random.randint(1, 2)):
                            try:
                                await asyncio.wait_for(
                                    human.deep_view_card(page, selector_index=idx, duration_seconds=random.uniform(40, 75)),
                                    timeout=120.0
                                )
                            except Exception:
                                pass
                            await asyncio.sleep(random.uniform(2.0, 5.0))

                    elif action == "search":
                        print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Поиск...{Style.RESET_ALL}")
                        query = random.choice(["питбайк", "мотоцикл", "квадроцикл", "эндуро", "авто", "ноутбук"])
                        
                        try:
                            await asyncio.wait_for(
                                page.goto("https://www.avito.ru/moskva/mototsikly_i_mototehnika", wait_until="networkidle", timeout=25000),
                                timeout=30.0
                            )
                            await asyncio.sleep(1.0)
                            
                            search = page.locator('input[data-marker="search-form/suggest"]').first
                            if await search.is_visible(timeout=2000):
                                await search.click()
                                await asyncio.sleep(0.5)
                                await search.fill("")
                                await human.type(page, 'input[data-marker="search-form/suggest"]', query, typos=True)
                                await asyncio.sleep(1.0)
                                
                                submit = page.locator('button[data-marker="search-form/submit"]').first
                                if await submit.is_visible(timeout=2000):
                                    await submit.click()
                                    try:
                                        await asyncio.wait_for(
                                            page.wait_for_load_state("networkidle", timeout=25000),
                                            timeout=30.0
                                        )
                                    except Exception:
                                        await asyncio.sleep(3.0)
                        except Exception:
                            pass

                    elif action == "browse":
                        print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Просмотр...{Style.RESET_ALL}")
                        try:
                            await asyncio.wait_for(
                                page.goto("https://www.avito.ru/moskva", wait_until="networkidle", timeout=25000),
                                timeout=30.0
                            )
                        except Exception:
                            pass
                        
                        await human.browse_page(page, duration_seconds=random.uniform(30, 60))

                    elif action == "favorites":
                        print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Просмотр избранного...{Style.RESET_ALL}")
                        try:
                            await asyncio.wait_for(
                                page.goto("https://www.avito.ru/moskva/mototsikly_i_mototehnika", wait_until="networkidle", timeout=25000),
                                timeout=30.0
                            )
                            await human.browse_page(page, duration_seconds=random.uniform(20, 40))
                        except Exception:
                            pass

                    elif action == "wait":
                        print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Отдых...{Style.RESET_ALL}")
                        await asyncio.sleep(random.uniform(5.0, 15.0))

                except asyncio.TimeoutError:
                    print(f"  {Fore.YELLOW}[Alive] Timeout{Style.RESET_ALL}")
                except Exception as e:
                    print(f"  {Fore.YELLOW}[Alive] Error: {str(e)[:50]}{Style.RESET_ALL}")

                # Большая пауза перед следующим действием
                self.iteration_count += 1
                pause = random.uniform(600, 3600)  # 10-60 минут
                print(f"  {Fore.CYAN}[Alive] Пауза {pause/60:.1f} мин (итерация #{self.iteration_count})...{Style.RESET_ALL}")
                
                try:
                    await asyncio.sleep(pause)
                except asyncio.CancelledError:
                    break

        except Exception as e:
            self.logger.error(account_id, f"Alive Mode error: {e}", severity="MEDIUM")
        finally:
            self.running = False
            print(f"  {Fore.YELLOW}[Alive] Остановлен{Style.RESET_ALL}")

    def stop(self):
        """Остановить Alive Mode"""
        self.running = False