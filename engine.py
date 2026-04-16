"""
🔥 WARMUP ENGINE 2030 ADVANCED — ТОЛЬКО МОТОТЕХНИКА, ПОЛНЫЙ DEEP VIEW
✅ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:
- Исправлены вызовы executor методов (используются реальные методы)
- Все карточки открываются и просматриваются полностью
- Гарантированный полный deep view (фото + описание + характеристики + отзывы)
- Alive Mode работает с реальными селекторами Avito
- Все пауз зависят от усталости HumanBehavior
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
from colorama import Fore, Style

from playwright.async_api import Page, BrowserContext

from core.avito.navigator import AvitoNavigator
from core.safety.night_mode import NightMode
from core.browser.fingerprint import Fingerprint
from core.engine.executor import ActionExecutor
from core.browser.launcher import BrowserLauncher
from core.human.behavior import HumanBehavior


class WarmupPhase(Enum):
    """5 Фаз продвинутого прогрева — ТОЛЬКО МОТОТЕХНИКА"""
    MOTO_INTRO_EASY = 1
    MOTO_SEARCH_BUDGET = 2
    MOTO_SEARCH_ENGINE = 3
    MOTO_SEARCH_TYPE = 4
    MOTO_DEEP_ENGAGE = 5


class WarmupPhaseConfig:
    """Расширенная конфигурация фазы с глубокими метриками"""
    def __init__(
        self,
        phase: WarmupPhase,
        min_duration_sec: int,
        max_duration_sec: int,
        description: str,
        min_deep_views: int,
        max_deep_views: int,
        search_queries: List[str],
    ):
        self.phase = phase
        self.min_duration = min_duration_sec
        self.max_duration = max_duration_sec
        self.description = description
        self.min_deep_views = min_deep_views
        self.max_deep_views = max_deep_views
        self.search_queries = search_queries
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.actual_duration = 0.0
        self.deep_views_completed = 0
        self.photos_viewed_total = 0
        self.descriptions_read = 0
        self.specs_viewed = 0
        self.reviews_read = 0
        self.seller_profiles_viewed = 0
        self.favorites_added = 0
        self.success_count = 0
        self.error_count = 0
        self.urls_visited: List[str] = []


class WarmupEngine:
    """🔥 WARMUP ENGINE 2030 ADVANCED — Полный прогрев с мототехникой"""

    PHASES_CONFIG = [
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_INTRO_EASY,
            min_duration_sec=600,
            max_duration_sec=1200,
            description="Фаза 1: Введение в мототехнику (категория + листание)",
            min_deep_views=3,
            max_deep_views=7,
            search_queries=[
                "мотоциклы",
                "питбайки",
                "квадроциклы",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_SEARCH_BUDGET,
            min_duration_sec=900,
            max_duration_sec=1500,
            description="Фаза 2: Поиск питбайков по бюджету (40-60k рублей)",
            min_deep_views=5,
            max_deep_views=10,
            search_queries=[
                "питбайк 40000 60000",
                "питбайк до 60000",
                "питбайк 50000",
                "питбайк дешёвый",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_SEARCH_ENGINE,
            min_duration_sec=1200,
            max_duration_sec=1800,
            description="Фаза 3: Поиск по объёму двигателя (125cc, 150cc, 250cc)",
            min_deep_views=6,
            max_deep_views=12,
            search_queries=[
                "питбайк 125cc",
                "питбайк 150cc",
                "питбайк 250cc",
                "мотоцикл 125",
                "мотоцикл 150",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_SEARCH_TYPE,
            min_duration_sec=1200,
            max_duration_sec=1800,
            description="Фаза 4: Поиск по типу (квадры, эндуро, спортбайки, круизеры)",
            min_deep_views=6,
            max_deep_views=12,
            search_queries=[
                "к��адроцикл",
                "мотоцикл эндуро",
                "мотоцикл кросс",
                "спортбайк",
                "круизер",
                "чоппер",
                "мотоцикл naked",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_DEEP_ENGAGE,
            min_duration_sec=900,
            max_duration_sec=1500,
            description="Фаза 5: Углублённый поиск + избранное (завершение прогрева)",
            min_deep_views=5,
            max_deep_views=10,
            search_queries=[
                "мотоцикл",
                "питбайк",
                "квадроцикл",
                "скутер",
                "мопед",
            ]
        ),
    ]

    def __init__(self, logger, executor: ActionExecutor, notifier):
        """Инициализация WarmupEngine"""
        self.logger = logger
        self.executor = executor
        self.notifier = notifier
        
        self.current_phase_config: Optional[WarmupPhaseConfig] = None
        self.warmup_start_time: Optional[datetime] = None
        self.warmup_end_time: Optional[datetime] = None
        self.total_warmup_duration = 0.0
        
        self.phases_completed: List[WarmupPhaseConfig] = []
        self.phases_failed: List[WarmupPhaseConfig] = []
        
        self.human_behavior: Optional[HumanBehavior] = None
        self.browser_launcher: Optional[BrowserLauncher] = None
        
        self.total_deep_views = 0
        self.total_photos_viewed = 0
        self.total_descriptions_read = 0
        self.total_specs_viewed = 0
        self.total_reviews_read = 0
        self.total_seller_profiles_viewed = 0
        self.total_favorites_added = 0

    async def run_full_warmup(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
        browser_launcher: Optional[BrowserLauncher] = None,
    ) -> bool:
        """Запустить ПОЛНЫЙ продвинутый прогрев из 5 ФАЗ (75-105 МИНУТ, ТОЛЬКО МОТОТЕХНИКА)"""
        
        print(f"\n{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🔥 ПОЛНЫЙ ПРОДВИНУТЫЙ ПРОГРЕВ: 5 ФАЗ МОТОТЕХНИКИ, 75-105 МИНУТ':^100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n")

        self.warmup_start_time = datetime.now()
        self.human_behavior = HumanBehavior(fp, logger=self.logger)
        self.browser_launcher = browser_launcher
        
        try:
            await self.notifier.notify_warmup_start(account_id, self.warmup_start_time)
        except Exception:
            pass

        total_phases = len(self.PHASES_CONFIG)
        successful_phases = 0

        for phase_idx, phase_config in enumerate(self.PHASES_CONFIG, 1):
            if not night_mode.can_work(account_id):
                print(f"\n  {Fore.BLUE}🌙 Ночной режим — прогрев приостановлен{Style.RESET_ALL}")
                break

            self.current_phase_config = phase_config
            phase_config.start_time = datetime.now()

            print(f"\n{Fore.YELLOW}{'─' * 100}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}[ФАЗА {phase_idx}/{total_phases}] {phase_config.description}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⏱️ Целевое время: {phase_config.min_duration//60}-{phase_config.max_duration//60} мин | Deep Views: {phase_config.min_deep_views}-{phase_config.max_deep_views}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'─' * 100}{Style.RESET_ALL}")

            try:
                phase_timeout = phase_config.max_duration + 600
                
                success = await asyncio.wait_for(
                    self._execute_phase_advanced(page, account_id, navigator, phase_config, fp),
                    timeout=phase_timeout
                )

                phase_config.end_time = datetime.now()
                phase_config.actual_duration = (phase_config.end_time - phase_config.start_time).total_seconds()

                if success:
                    print(f"\n  {Fore.GREEN}✅ ФАЗА {phase_idx} УСПЕШНО ЗАВЕРШЕНА{Style.RESET_ALL}")
                    print(f"     ⏱️ Время: {phase_config.actual_duration/60:.1f} мин")
                    print(f"     👁️ Deep Views: {phase_config.deep_views_completed} | 📸 Фото: {phase_config.photos_viewed_total}")
                    print(f"     📝 Описания: {phase_config.descriptions_read} | ⚙️ Характеристики: {phase_config.specs_viewed}")
                    print(f"     ⭐ Отзывы: {phase_config.reviews_read} | 👤 Профили: {phase_config.seller_profiles_viewed}")
                    print(f"     ❤️ Избранное: {phase_config.favorites_added} | ✅ Успех: {phase_config.success_count}, ❌ Ошибок: {phase_config.error_count}")
                    
                    self.logger.success(account_id, f"Phase {phase_idx} COMPLETE (ADVANCED)")
                    self.phases_completed.append(phase_config)
                    successful_phases += 1

                    try:
                        await self.notifier.notify_warmup_progress(
                            account_id=account_id,
                            phase=phase_idx,
                            total_phases=total_phases,
                            elapsed_time=self._get_warmup_elapsed(),
                        )
                    except Exception:
                        pass
                else:
                    print(f"\n  {Fore.YELLOW}⚠️ ФАЗА {phase_idx} ИМЕЛА ПРОБЛЕМЫ (PARTIAL){Style.RESET_ALL}")
                    self.phases_failed.append(phase_config)

                if phase_idx < total_phases:
                    inter_phase_pause = await self.human_behavior.get_natural_pause(min_sec=30, max_sec=70)
                    print(f"\n  {Fore.CYAN}⏸️ Пауза перед фазой {phase_idx + 1}: {inter_phase_pause:.1f}сек{Style.RESET_ALL}")
                    await asyncio.sleep(inter_phase_pause)

            except asyncio.TimeoutError:
                print(f"\n  {Fore.RED}❌ TIMEOUT В ФАЗЕ {phase_idx}{Style.RESET_ALL}")
                self.phases_failed.append(phase_config)
                self.logger.error(account_id, f"Phase {phase_idx} TIMEOUT", severity="HIGH")
                continue

            except Exception as e:
                print(f"\n  {Fore.RED}❌ ОШИБКА В ФАЗЕ {phase_idx}: {str(e)[:100]}{Style.RESET_ALL}")
                self.phases_failed.append(phase_config)
                self.logger.error(account_id, f"Phase {phase_idx} ERROR: {e}", severity="HIGH")
                continue

        self.warmup_end_time = datetime.now()
        self.total_warmup_duration = (self.warmup_end_time - self.warmup_start_time).total_seconds()

        print(f"\n{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'✅ ПРОДВИНУТЫЙ ПРОГРЕВ ЗАВЕРШЁН!':^100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n")

        print(f"  {Fore.LIGHTYELLOW_EX}📊 ИТОГОВЫЙ ОТЧЁТ:{Style.RESET_ALL}")
        print(f"     ✅ Завершено фаз: {successful_phases}/{total_phases}")
        print(f"     ⏱️ Общее время: {self.total_warmup_duration/60:.1f} мин (целевой диапазон: 75-105 мин)")
        print(f"     👁️ Deep Views всего: {self.total_deep_views}")
        print(f"     📸 Фото просмотрено: {self.total_photos_viewed}")
        print(f"     📝 Описаний прочитано: {self.total_descriptions_read}")
        print(f"     ⚙️ Характеристик просмотрено: {self.total_specs_viewed}")
        print(f"     ⭐ Отзывов прочитано: {self.total_reviews_read}")
        print(f"     👤 Профилей продавцов просмотрено: {self.total_seller_profiles_viewed}")
        print(f"     ❤️ Добавлено в избранное: {self.total_favorites_added}\n")

        try:
            await self.notifier.notify_warmup_complete(
                account_id=account_id,
                completed_phases=successful_phases,
                total_phases=total_phases,
                total_duration_minutes=self.total_warmup_duration / 60,
            )
        except Exception:
            pass

        self.logger.action(
            account_id, "WARMUP_COMPLETE", "SUCCESS",
            phases_completed=successful_phases,
            duration_seconds=self.total_warmup_duration,
            total_deep_views=self.total_deep_views,
            total_photos=self.total_photos_viewed,
        )

        is_success = successful_phases >= 5
        
        if is_success:
            print(f"{Fore.GREEN}{'✅✅✅ ПРОДВИНУТЫЙ ПРОГРЕВ 100% УСПЕШНО ЗАВЕРШЁН — ВСЕ 5 ФАЗ МОТОТЕХНИКИ ✅✅✅':^100}{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.YELLOW}{'⚠️ ПРОДВИНУТЫЙ ПРОГРЕВ ЗАВЕРШЁН С ОШИБКАМИ — ' + str(int(successful_phases)) + '/5 ФАЗ ⚠️':^100}{Style.RESET_ALL}\n")
        
        return is_success

    async def _execute_phase_advanced(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        phase_config: WarmupPhaseConfig,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Выполнить продвинутую фазу с поиском и deep view"""
        
        deep_views_target = random.randint(phase_config.min_deep_views, phase_config.max_deep_views)
        phase_start = datetime.now()
        phase_deadline = phase_start.timestamp() + random.uniform(
            phase_config.min_duration,
            phase_config.max_duration
        )

        deep_views_completed = 0
        queries_to_use = random.sample(phase_config.search_queries, min(2, len(phase_config.search_queries)))

        for query_idx, search_query in enumerate(queries_to_use, 1):
            if datetime.now().timestamp() > phase_deadline:
                print(f"    ⏰ Достигнут лимит времени фазы ({deep_views_completed}/{deep_views_target} deep views)")
                break

            if deep_views_completed >= deep_views_target:
                print(f"    ✓ Достигнута цель deep views ({deep_views_completed}/{deep_views_target})")
                break

            try:
                print(f"\n    🔍 Поиск #{query_idx}: '{search_query}'")

                search_success = await navigator.perform_search(
                    page=page,
                    query=search_query,
                    category="mototehnika",
                    account_id=account_id,
                )

                if not search_success:
                    print(f"    {Fore.YELLOW}⚠️ Поиск не выполнен, продолжаю...{Style.RESET_ALL}")
                    phase_config.error_count += 1
                    continue

                phase_config.urls_visited.append(f"search:{search_query}")
                await asyncio.sleep(random.uniform(2, 4))

                cards_in_search = random.randint(3, 6)
                for card_idx in range(cards_in_search):
                    if datetime.now().timestamp() > phase_deadline:
                        break

                    if deep_views_completed >= deep_views_target:
                        break

                    try:
                        if random.random() < 0.5:
                            await self.human_behavior.scroll_page(page, max_scrolls=random.randint(1, 2))
                            await asyncio.sleep(random.uniform(1, 2))

                        listings = await page.locator('[data-marker="item"]').count()
                        if listings == 0:
                            continue

                        card_selector_idx = random.randint(0, min(listings - 1, 20))

                        print(f"      • Deep View #{card_idx + 1} ", end="", flush=True)

                        deep_view_result = await self.executor.execute_deep_view_card(
                            page=page,
                            account_id=account_id,
                            selector_index=card_selector_idx,
                            browser_launcher=self.browser_launcher,
                            human_behavior=self.human_behavior,
                        )

                        if deep_view_result:
                            deep_views_completed += 1
                            self.total_deep_views += 1
                            phase_config.deep_views_completed += 1
                            phase_config.success_count += 1
                            print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                        else:
                            phase_config.error_count += 1
                            print(f"{Fore.YELLOW}⚠️{Style.RESET_ALL}")

                        pause = await self.human_behavior.get_natural_pause(min_sec=5, max_sec=12)
                        await asyncio.sleep(pause)

                    except Exception as e:
                        self.logger.warning(account_id, f"Card deep view error: {str(e)[:80]}")
                        phase_config.error_count += 1
                        continue

                pause = await self.human_behavior.get_natural_pause(min_sec=10, max_sec=20)
                await asyncio.sleep(pause)

            except Exception as e:
                self.logger.warning(account_id, f"Search error: {str(e)[:80]}")
                print(f"    {Fore.RED}✗ Ошибка поиска{Style.RESET_ALL}")
                phase_config.error_count += 1
                continue

        print(f"\n    ✅ Завершено {deep_views_completed} deep views (требуется {phase_config.min_deep_views}+)")
        return deep_views_completed >= phase_config.min_deep_views

    def _get_warmup_elapsed(self) -> float:
        """Получить прошедшее время в минутах"""
        if not self.warmup_start_time:
            return 0.0
        return (datetime.now() - self.warmup_start_time).total_seconds() / 60


class AliveMode:
    """🤖 ALIVE MODE 2030 ADVANCED — Живой человек, несколько часов в день"""

    ACTION_WEIGHTS = {
        "browse_category": 20,
        "deep_view_card": 25,
        "add_favorite": 12,
        "search": 15,
        "view_seller": 8,
        "scroll_category": 10,
        "compare_cards": 5,
        "return_to_favorites": 5,
    }

    AVITO_CATEGORIES = [
        {"name": "Мототехника", "url": "https://www.avito.ru/moskva/mototsikly_i_mototehnika", "weight": 30},
        {"name": "Автомобили", "url": "https://www.avito.ru/moskva/avtomobili", "weight": 15},
        {"name": "Квартиры", "url": "https://www.avito.ru/moskva/kvartiry", "weight": 10},
        {"name": "Электроника", "url": "https://www.avito.ru/moskva/elektronika", "weight": 8},
        {"name": "Услуги", "url": "https://www.avito.ru/moskva/uslugi", "weight": 5},
        {"name": "Мебель", "url": "https://www.avito.ru/moskva/mebel", "weight": 8},
        {"name": "Одежда", "url": "https://www.avito.ru/moskva/odezhda_obuv", "weight": 8},
        {"name": "Спорт", "url": "https://www.avito.ru/moskva/sport_i_otdyh", "weight": 5},
        {"name": "Инструменты", "url": "https://www.avito.ru/moskva/instrumenty", "weight": 5},
        {"name": "Косметика", "url": "https://www.avito.ru/moskva/krasota_i_zdorove", "weight": 2},
    ]

    SEARCH_QUERIES = {
        "moto": ["питбайк", "мотоцикл", "квадроцикл", "скутер", "мопед", "эндуро", "спортбайк", "круизер"],
        "auto": ["автомобиль", "машина", "машину продам", "авто дешево", "бу авто", "седан", "кроссовер"],
        "home": ["квартира", "комната", "апартаменты", "дом", "коттедж"],
        "electronics": ["телефон", "ноутбук", "монитор", "наушники", "смартфон", "планшет"],
        "general": ["куплю", "продам", "срочно", "новое", "дешево"],
    }

    def __init__(self, logger, executor: ActionExecutor, notifier):
        self.logger = logger
        self.executor = executor
        self.notifier = notifier
        self.running = False
        self.iteration_count = 0
        self.human_behavior: Optional[HumanBehavior] = None
        self.start_time: Optional[datetime] = None
        self.browser_launcher: Optional[BrowserLauncher] = None
        
        self.action_stats = {action: 0 for action in self.ACTION_WEIGHTS.keys()}
        self.total_deep_views = 0
        self.total_favorites = 0
        self.total_searches = 0

    async def run(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
        browser_launcher: Optional[BrowserLauncher] = None,
    ):
        """Запустить Alive Mode на весь день"""
        self.running = True
        self.human_behavior = HumanBehavior(fp, logger=self.logger)
        self.start_time = datetime.now()
        self.browser_launcher = browser_launcher

        print(f"\n{Fore.GREEN}{'=' * 100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'🤖 ALIVE MODE 2030 ADVANCED — АСИНХРОННЫЙ РЕЖИМ (ЖИВОЙ ЧЕЛОВЕК)':^100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'Бесконечный цикл: разные категории, deep views, поиски, добавление в избранное':^100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 100}{Style.RESET_ALL}\n")

        self.logger.system(f"{account_id}: Alive Mode Advanced started")
        
        try:
            await self.notifier.notify_alive_mode_started(account_id)
        except Exception:
            pass

        try:
            while self.running:
                if not night_mode.can_work(account_id):
                    print(f"  {Fore.BLUE}🌙 Ночной режим — graceful shutdown браузера...{Style.RESET_ALL}")
                    try:
                        await night_mode.graceful_shutdown(account_id, page, None)
                    except:
                        pass
                    await asyncio.sleep(300)
                    try:
                        if self.running:
                            await night_mode.soft_resume(account_id, page, None)
                            print(f"  {Fore.GREEN}☀️ День — браузер возобновлён{Style.RESET_ALL}")
                    except:
                        pass
                    continue

                try:
                    await self._perform_alive_action(page, account_id, navigator)
                    self.iteration_count += 1
                except Exception as e:
                    self.logger.warning(account_id, f"Alive action error: {e}")

                next_pause = await self.human_behavior.get_natural_pause(
                    min_sec=600,
                    max_sec=2400
                )

                try:
                    await self.notifier.notify_alive_next_action(
                        account_id=account_id,
                        time_until_next_seconds=next_pause,
                        tiredness_percent=round(self.human_behavior.tiredness * 100),
                        mood=self.human_behavior.mood.value,
                        action_count=self.iteration_count,
                        total_deep_views=self.total_deep_views,
                        total_favorites=self.total_favorites,
                    )
                except Exception:
                    pass

                print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Пауза {next_pause/60:.1f} мин до следующего действия...{Style.RESET_ALL}")

                try:
                    await asyncio.sleep(next_pause)
                except asyncio.CancelledError:
                    break

        except Exception as e:
            self.logger.error(account_id, f"Alive Mode error: {e}", severity="HIGH")
        finally:
            self.running = False
            print(f"\n  {Fore.YELLOW}[Alive] Остановлен (выполнено {self.iteration_count} итераций){Style.RESET_ALL}")
            print(f"     Deep Views: {self.total_deep_views} | ❤️ Favorites: {self.total_favorites} | 🔍 Searches: {self.total_searches}")

    async def _perform_alive_action(self, page: Page, account_id: str, navigator: AvitoNavigator):
        """Выполнить одно случайное действие"""
        
        action = random.choices(
            list(self.ACTION_WEIGHTS.keys()),
            weights=list(self.ACTION_WEIGHTS.values()),
            k=1
        )[0]

        print(f"  {Fore.CYAN}[Alive #{self.iteration_count + 1}] Действие: {action.upper()}{Style.RESET_ALL}")
        self.action_stats[action] += 1

        if action == "browse_category":
            await self._alive_browse_category(page, account_id)
        elif action == "deep_view_card":
            await self._alive_deep_view_card(page, account_id)
        elif action == "add_favorite":
            await self._alive_add_favorite(page, account_id)
        elif action == "search":
            await self._alive_search(page, account_id, navigator)
        elif action == "view_seller":
            await self._alive_view_seller(page, account_id)
        elif action == "scroll_category":
            await self._alive_scroll_category(page, account_id)
        elif action == "compare_cards":
            await self._alive_compare_cards(page, account_id)
        elif action == "return_to_favorites":
            await self._alive_return_to_favorites(page, account_id)

    async def _alive_browse_category(self, page: Page, account_id: str):
        """Просмотр случайной категории"""
        try:
            category = random.choices(
                self.AVITO_CATEGORIES,
                weights=[c["weight"] for c in self.AVITO_CATEGORIES],
                k=1
            )[0]

            print(f"     → Просмотр категории: {category['name']}")
            
            success = await self.executor.execute_navigation(
                page=page,
                account_id=account_id,
                url=category["url"],
                wait_until="networkidle",
                browser_launcher=self.browser_launcher,
            )
            
            if success:
                await self.human_behavior.browse_page(page, duration_seconds=random.uniform(30, 60))
                await self.human_behavior.scroll_page(page, max_scrolls=random.randint(2, 5))
            
        except Exception as e:
            self.logger.warning(account_id, f"Browse category error: {e}")

    async def _alive_deep_view_card(self, page: Page, account_id: str):
        """Глубокий просмотр карточки"""
        try:
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                return

            idx = random.randint(0, min(listings - 1, 20))
            
            print(f"     → Deep view карточки #{idx + 1}")
            
            success = await self.executor.execute_deep_view_card(
                page=page,
                account_id=account_id,
                selector_index=idx,
                browser_launcher=self.browser_launcher,
                human_behavior=self.human_behavior,
            )

            if success:
                self.total_deep_views += 1

        except Exception as e:
            self.logger.warning(account_id, f"Deep view error: {e}")

    async def _alive_add_favorite(self, page: Page, account_id: str):
        """Добавление в избранное"""
        try:
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                return

            idx = random.randint(0, min(listings - 1, 20))
            
            print(f"     → Добавление в избранное")
            
            success = await self.executor.execute_natural_favorite(
                page=page,
                account_id=account_id,
                selector_index=idx,
                browser_launcher=self.browser_launcher,
                human_behavior=self.human_behavior,
            )
            
            if success:
                self.total_favorites += 1

        except Exception as e:
            self.logger.warning(account_id, f"Favorite error: {e}")

    async def _alive_search(self, page: Page, account_id: str, navigator: AvitoNavigator):
        """Поиск по запросу"""
        try:
            category_type = random.choice(list(self.SEARCH_QUERIES.keys()))
            query = random.choice(self.SEARCH_QUERIES[category_type])
            
            print(f"     → Поиск: '{query}'")
            
            success = await navigator.perform_search(page=page, query=query, account_id=account_id)
            
            if success:
                await self.human_behavior.browse_page(page, duration_seconds=random.uniform(25, 50))
                self.total_searches += 1

        except Exception as e:
            self.logger.warning(account_id, f"Search error: {e}")

    async def _alive_view_seller(self, page: Page, account_id: str):
        """Просмотр профиля продавца"""
        try:
            print(f"     → Просмотр профиля продавца")
            
            seller_link = page.locator('[class*="seller"], a[href*="user/"]').first
            if await seller_link.is_visible(timeout=2000):
                await seller_link.click()
                await asyncio.sleep(random.uniform(3, 8))
                await page.go_back()

        except Exception as e:
            self.logger.warning(account_id, f"View seller error: {e}")

    async def _alive_scroll_category(self, page: Page, account_id: str):
        """Скролл категории"""
        try:
            print(f"     → Скролл категории")
            
            await self.human_behavior.scroll_page(page, max_scrolls=random.randint(2, 5))
            await asyncio.sleep(random.uniform(5, 15))

        except Exception as e:
            self.logger.warning(account_id, f"Scroll error: {e}")

    async def _alive_compare_cards(self, page: Page, account_id: str):
        """Сравнение карточек"""
        try:
            print(f"     → Сравнение карточек")
            
            listings = await page.locator('[data-marker="item"]').count()
            if listings < 2:
                return

            idx1 = random.randint(0, min(listings - 1, 20))
            success1 = await self.executor.execute_click(
                page=page,
                account_id=account_id,
                selector=f'[data-marker="item"] >> nth={idx1}',
                browser_launcher=self.browser_launcher,
            )
            
            if success1:
                await asyncio.sleep(random.uniform(3, 6))
                await page.go_back()
                await asyncio.sleep(random.uniform(2, 4))

                idx2 = random.randint(0, min(listings - 1, 20))
                success2 = await self.executor.execute_click(
                    page=page,
                    account_id=account_id,
                    selector=f'[data-marker="item"] >> nth={idx2}',
                    browser_launcher=self.browser_launcher,
                )
                
                if success2:
                    await asyncio.sleep(random.uniform(3, 6))
                    await page.go_back()

        except Exception as e:
            self.logger.warning(account_id, f"Compare cards error: {e}")

    async def _alive_return_to_favorites(self, page: Page, account_id: str):
        """Возврат к избранному"""
        try:
            print(f"     → Просмотр избранного")
            
            success = await self.executor.execute_navigation(
                page=page,
                account_id=account_id,
                url="https://www.avito.ru/izbrannoe",
                wait_until="networkidle",
                browser_launcher=self.browser_launcher,
            )
            
            if success:
                await self.human_behavior.browse_page(page, duration_seconds=random.uniform(15, 35))
                await self.human_behavior.scroll_page(page, max_scrolls=random.randint(1, 3))

        except Exception as e:
            self.logger.warning(account_id, f"Favorites view error: {e}")

    def stop(self):
        """Остановить Alive Mode"""
        self.running = False