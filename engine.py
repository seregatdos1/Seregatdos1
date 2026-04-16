# core/warmup/engine.py
"""
🔥 WARMUP ENGINE — ПОЛНЫЙ И РАБОЧИЙ ПРОГРЕВ АККАУНТА
5 фаз с полной защитой от ошибок, обработкой timeout, anti-detection
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
    """Полный прогрев аккаунта"""

    def __init__(self, logger):
        self.logger = logger

    async def run_full_warmup(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Запустить полный прогрев из 5 фаз"""
        print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🔥 НАЧИНАЕТСЯ ПРОГРЕВ АККАУНТА (5 ФАЗ)':^70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

        phases = [
            ("Фаза 1: Внешние сайты", self._phase_external_sites),
            ("Фаза 2: Avito категории", self._phase_avito_categories),
            ("Фаза 3: Профиль", self._phase_profile),
            ("Фаза 4: Интенсивный просмотр", self._phase_intensive),
            ("Фаза 5: Режим покупателя", self._phase_buyer_mode),
        ]

        completed_phases = 0

        for phase_num, (phase_name, phase_func) in enumerate(phases, 1):
            # Проверяем ночной режим перед каждой фазой
            if not night_mode.can_work(account_id):
                print(f"\n  {Fore.BLUE}🌙 Ночной режим активен — прогрев приостановлен на фазе {phase_num}{Style.RESET_ALL}")
                self.logger.warning(account_id, f"Warmup paused by night mode at phase {phase_num}")
                break

            print(f"\n  {Fore.YELLOW}🔥 {phase_name}...{Style.RESET_ALL}")

            try:
                # Запускаем фазу с timeout 15 минут
                success = await asyncio.wait_for(
                    phase_func(page, account_id, navigator, fp),
                    timeout=900.0
                )

                if success:
                    print(f"  {Fore.GREEN}✅ {phase_name} завершена{Style.RESET_ALL}")
                    self.logger.success(account_id, phase_name)
                    completed_phases += 1
                else:
                    print(f"  {Fore.YELLOW}⚠️ {phase_name} имела проблемы{Style.RESET_ALL}")
                    self.logger.warning(account_id, f"{phase_name} had issues")
                    completed_phases += 1

                # Пауза между фазами (зависит от усталости)
                pause = random.uniform(8.0, 20.0)
                print(f"  {Fore.CYAN}⏱️ Пауза {pause:.1f}с перед следующей фазой...{Style.RESET_ALL}")
                await asyncio.sleep(pause)

            except asyncio.TimeoutError:
                print(f"  {Fore.RED}❌ Timeout в {phase_name} (>15 мин){Style.RESET_ALL}")
                self.logger.error(account_id, f"{phase_name} timeout", severity="HIGH")
                # Продолжаем на следующую фазу
                continue

            except Exception as e:
                print(f"  {Fore.RED}❌ Ошибка в {phase_name}: {str(e)[:100]}{Style.RESET_ALL}")
                self.logger.error(account_id, f"Error in {phase_name}: {e}", severity="HIGH")
                # Продолжаем на следующую фазу
                continue

        print(f"\n  {Fore.GREEN}{'=' * 70}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}{'✅ ПРОГРЕВ ЗАВЕРШЁН! Завершено фаз: ' + str(completed_phases) + '/5':^70}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}{'=' * 70}{Style.RESET_ALL}\n")

        self.logger.action(account_id, "WARMUP_COMPLETE", "SUCCESS", phases_completed=completed_phases)
        
        # Прогрев считается успешным если прошли минимум 3 фазы
        return completed_phases >= 3

    async def _phase_external_sites(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Фаза 1: Посещение внешних сайтов"""
        human = HumanBehavior(fp)
        sites = [
            "https://www.google.ru",
            "https://www.yandex.ru",
            "https://ru.wikipedia.org",
        ]

        for site in sites:
            try:
                print(f"    → {site[:40]}...", end=" ", flush=True)
                
                # Используем timeout для goto
                try:
                    await asyncio.wait_for(
                        page.goto(site, wait_until="networkidle", timeout=15000),
                        timeout=20.0
                    )
                    print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                except asyncio.TimeoutError:
                    print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
                
                # Просмотр страницы
                await human.browse_page(page, duration_seconds=random.uniform(15, 35))
                
                # Пауза перед следующим сайтом
                await asyncio.sleep(random.uniform(2.0, 5.0))

            except Exception as e:
                print(f"{Fore.RED}✗{Style.RESET_ALL}")
                self.logger.warning(account_id, f"External site error: {site}")
                continue

        return True

    async def _phase_avito_categories(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Фаза 2: Просмотр категорий Avito"""
        human = HumanBehavior(fp)

        categories = [
            ("Автомобили", "https://www.avito.ru/moskva/avtomobili"),
            ("Мотоциклы", "https://www.avito.ru/moskva/mototsikly_i_mototehnika"),
            ("Запчасти", "https://www.avito.ru/moskva/zapchasti_i_aksessuary"),
            ("Коллекции", "https://www.avito.ru/moskva/kollektsii"),
        ]

        for cat_name, category_url in categories:
            try:
                print(f"    → {cat_name:20}", end=" ", flush=True)
                
                try:
                    await asyncio.wait_for(
                        page.goto(category_url, wait_until="networkidle", timeout=15000),
                        timeout=20.0
                    )
                    print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                except asyncio.TimeoutError:
                    print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
                
                # Просмотр категории
                await human.browse_page(page, duration_seconds=random.uniform(20, 40))
                
                # Скролл объявлений
                await human.scroll_page(page, max_scrolls=random.randint(2, 5))
                
                # Пауза
                await asyncio.sleep(random.uniform(3.0, 8.0))

            except Exception as e:
                print(f"{Fore.RED}✗{Style.RESET_ALL}")
                self.logger.warning(account_id, f"Category error: {cat_name}")
                continue

        return True

    async def _phase_profile(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Фаза 3: Просмотр профиля и личных данных"""
        human = HumanBehavior(fp)

        try:
            print(f"    → Профиль", end=" ", flush=True)
            
            try:
                await asyncio.wait_for(
                    page.goto(AvitoUrls.PROFILE, wait_until="networkidle", timeout=15000),
                    timeout=20.0
                )
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
            
            # Просмотр профиля
            await human.browse_page(page, duration_seconds=random.uniform(25, 45))
            
            # Проверяем информацию о продавце если есть
            try:
                await asyncio.wait_for(
                    human.check_seller_info(page),
                    timeout=10.0
                )
            except Exception:
                pass
            
            await asyncio.sleep(random.uniform(2.0, 5.0))
            
            return True
        except Exception as e:
            self.logger.warning(account_id, f"Profile phase error: {e}")
            return False

    async def _phase_intensive(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Фаза 4: Интенсивный просмотр объявлений"""
        human = HumanBehavior(fp)
        max_iterations = random.randint(5, 10)
        success_count = 0

        for i in range(max_iterations):
            try:
                print(f"    → Итерация {i+1}/{max_iterations}", end=" ", flush=True)
                
                # Если мы не на главной - идём туда
                if "avito.ru" not in page.url:
                    try:
                        await asyncio.wait_for(
                            page.goto(AvitoUrls.BASE, wait_until="networkidle", timeout=15000),
                            timeout=20.0
                        )
                    except Exception:
                        pass
                
                # Просмотр
                await human.browse_page(page, duration_seconds=random.uniform(12, 25))
                
                # Скролл
                await human.scroll_page(page, max_scrolls=random.randint(1, 3))
                
                # Случайное действие
                await human.random_human_action(page)
                
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                success_count += 1
                
                await asyncio.sleep(random.uniform(1.0, 3.0))

            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
                continue
            except Exception as e:
                print(f"{Fore.RED}✗{Style.RESET_ALL}")
                continue

        return success_count > 0

    async def _phase_buyer_mode(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """Фаза 5: Режим активного покупателя"""
        human = HumanBehavior(fp)
        max_iterations = random.randint(3, 7)
        success_count = 0

        for i in range(max_iterations):
            try:
                print(f"    → Действие {i+1}/{max_iterations}", end=" ", flush=True)
                
                # Главная страница
                if "avito.ru" not in page.url or random.random() < 0.3:
                    try:
                        await asyncio.wait_for(
                            page.goto(AvitoUrls.BASE, wait_until="networkidle", timeout=15000),
                            timeout=20.0
                        )
                    except Exception:
                        pass
                
                # Просмотр изображений
                try:
                    await asyncio.wait_for(
                        human.inspect_images(page, max_images=random.randint(1, 4)),
                        timeout=15.0
                    )
                except Exception:
                    pass
                
                # Скролл
                await human.scroll_page(page, max_scrolls=random.randint(1, 3))
                
                # Попытка кликнуть на объявление
                try:
                    listings_count = await page.locator('[data-marker="item"]').count()
                    if listings_count > 0:
                        idx = random.randint(0, min(listings_count - 1, 10))
                        await page.locator('[data-marker="item"]').nth(idx).click()
                        await asyncio.sleep(random.uniform(2.0, 5.0))
                        
                        # Иногда кликаем избранное
                        if random.random() < 0.3:
                            try:
                                fav_btn = page.locator('[data-marker="favorite-button"]').first
                                if await fav_btn.is_visible(timeout=1000):
                                    await fav_btn.click()
                            except Exception:
                                pass
                        
                        # Возвращаемся назад
                        await page.go_back()
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                except Exception:
                    pass
                
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                success_count += 1
                
                await asyncio.sleep(random.uniform(1.0, 3.0))

            except asyncio.TimeoutError:
                print(f"{Fore.YELLOW}⏱️{Style.RESET_ALL}")
                continue
            except Exception as e:
                print(f"{Fore.RED}✗{Style.RESET_ALL}")
                continue

        return success_count > 0


class AliveMode:
    """Alive Mode - фоновая активность"""

    def __init__(self, logger):
        self.logger = logger
        self.running = False
        self.iteration_count = 0

    async def run(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
    ):
        """Запустить Alive Mode - фоновая активность на бесконечность"""
        self.running = True
        human = HumanBehavior(fp)

        print(f"\n{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'✅ ALIVE MODE ЗАПУЩЕН':^70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}\n")

        self.logger.system(f"{account_id}: Alive Mode started")

        try:
            while self.running:
                # Проверяем ночной режим
                if not night_mode.can_work(account_id):
                    print(f"  {Fore.BLUE}🌙 Ночной режим - ожидание...{Style.RESET_ALL}")
                    await asyncio.sleep(300)
                    continue

                # Выбираем случайное действие
                action = random.choice([
                    "browse",
                    "search",
                    "scroll",
                    "images",
                    "random",
                    "wait",
                ])

                try:
                    if action == "browse":
                        print(f"  {Fore.CYAN}[Alive] Просмотр главной...{Style.RESET_ALL}")
                        try:
                            await asyncio.wait_for(
                                page.goto(AvitoUrls.BASE, wait_until="networkidle", timeout=15000),
                                timeout=20.0
                            )
                        except Exception:
                            pass
                        await human.browse_page(page, duration_seconds=random.uniform(15, 40))

                    elif action == "search":
                        print(f"  {Fore.CYAN}[Alive] Поиск...{Style.RESET_ALL}")
                        query = random.choice(["кв", "авто", "велосипед", "ноутбук"])
                        try:
                            await asyncio.wait_for(
                                human.fill_search(page, query),
                                timeout=15.0
                            )
                        except Exception:
                            pass

                    elif action == "scroll":
                        print(f"  {Fore.CYAN}[Alive] Скролл...{Style.RESET_ALL}")
                        await human.scroll_page(page, max_scrolls=random.randint(2, 5))

                    elif action == "images":
                        print(f"  {Fore.CYAN}[Alive] Просмотр фото...{Style.RESET_ALL}")
                        try:
                            await asyncio.wait_for(
                                human.inspect_images(page, max_images=random.randint(2, 5)),
                                timeout=15.0
                            )
                        except Exception:
                            pass

                    elif action == "random":
                        print(f"  {Fore.CYAN}[Alive] Случайное действие...{Style.RESET_ALL}")
                        await human.random_human_action(page)

                    elif action == "wait":
                        print(f"  {Fore.CYAN}[Alive] Отдых...{Style.RESET_ALL}")
                        await asyncio.sleep(random.uniform(2.0, 5.0))

                except asyncio.TimeoutError:
                    print(f"  {Fore.YELLOW}[Alive] Timeout{Style.RESET_ALL}")
                except Exception as e:
                    print(f"  {Fore.YELLOW}[Alive] Error: {str(e)[:50]}{Style.RESET_ALL}")

                # Большая пауза перед следующим действием (10-40 минут)
                self.iteration_count += 1
                pause = random.uniform(600, 2400)
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