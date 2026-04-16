# core/avito/login.py
"""
🔐 LOGIN ENGINE 2030 — АВТОРИЗАЦИЯ НА AVITO
Вход с сохранённой сессией, SMS, автоматическое определение статуса
Production ready, без сокращений
"""

import asyncio
from typing import Optional
from colorama import Fore, Style


async def login_with_session(
    page,
    account_id: str,
    navigator,
    logger,
    timeout: int = 30
) -> bool:
    """
    Попытка входа с сохранённой сессией
    
    Процесс:
    1. Переходим на Avito
    2. Проверяем, уже ли авторизированы
    3. Если да — возвращаем True
    4. Если нет — возвращаем False (нужна SMS)
    
    Args:
        page: Playwright Page
        account_id: ID аккаунта
        navigator: AvitoNavigator
        logger: Logger
        timeout: Таймаут в секундах
        
    Returns:
        True если авторизированы, False если нужна SMS
    """
    
    try:
        logger.info(account_id, "Проверяю сохранённую сессию")
        
        # ─────────────────────────────────────────────────────
        # 1. ПЕРЕХОДИМ НА ГЛАВНУЮ СТРАНИЦУ
        # ─────────────────────────────────────────────────────
        
        try:
            await page.goto(
                "https://www.avito.ru/",
                wait_until="domcontentloaded",
                timeout=15000
            )
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(account_id, f"Failed to load main page: {e}")
            return False
        
        # ─────────────────────────────────────────────────────
        # 2. ПРОВЕРЯЕМ АВТОРИЗАЦИЮ
        # ─────────────────────────────────────────────────────
        
        # Способ 1: Проверяем наличие кнопки "Мой профиль"
        try:
            profile_button = page.locator('[data-marker="user-profile-button"]')
            if await profile_button.is_visible(timeout=3000):
                logger.success(account_id, "Already logged in (method 1)")
                return True
        except Exception:
            pass
        
        # Способ 2: Проверяем URL профиля
        try:
            await page.goto(
                "https://www.avito.ru/profile",
                wait_until="domcontentloaded",
                timeout=10000
            )
            await asyncio.sleep(1)
            
            # Если не редирект на логин — авторизированы
            current_url = page.url
            if "profile" in current_url and "login" not in current_url:
                logger.success(account_id, "Already logged in (method 2)")
                return True
        except Exception as e:
            logger.warning(account_id, f"Profile check failed: {e}")
        
        # Способ 3: Проверяем наличие элементов профиля
        try:
            user_name = page.locator('[data-marker="user-name"]')
            if await user_name.is_visible(timeout=2000):
                logger.success(account_id, "Already logged in (method 3)")
                return True
        except Exception:
            pass
        
        logger.warning(account_id, "Not logged in, need SMS")
        return False
    
    except Exception as e:
        logger.error(account_id, f"Session check error: {e}", severity="MEDIUM")
        return False


async def login_with_sms(
    page,
    account_id: str,
    phone: str,
    navigator,
    logger,
    notifier,
    fp,
    timeout: int = 120
) -> bool:
    """
    Вход через SMS с АВТОМАТИЧЕСКИМ ОПРЕДЕЛЕНИЕМ СТАТУСА
    
    Процесс:
    1. Переходим на страницу логина
    2. Вводим номер телефона
    3. Запрашиваем SMS
    4. ЖДЁМ АВТОМАТИЧЕСКОГО ВВОДА КОДА (Avito может автоматически заполнить)
    5. После ввода кода проверяем авторизацию
    
    Args:
        page: Playwright Page
        account_id: ID аккаунта
        phone: Номер телефона
        navigator: AvitoNavigator
        logger: Logger
        notifier: TelegramNotifier
        fp: Fingerprint
        timeout: Таймаут ввода кода в секундах
        
    Returns:
        True если авторизированы, False если ошибка
    """
    
    try:
        logger.info(account_id, f"Начинаю вход через SMS: {phone}")
        
        # ─────────────────────────────────────────────────────
        # 1. ПЕРЕХОДИМ НА СТРАНИЦУ ЛОГИНА
        # ─────────────────────────────────────────────────────
        
        try:
            await page.goto(
                "https://www.avito.ru/profile",
                wait_until="domcontentloaded",
                timeout=15000
            )
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(account_id, f"Failed to load profile page: {e}")
            return False
        
        # ─────────────────────────────────────────────────────
        # 2. ПРОВЕРЯЕМ, МОЖЕт ЛИ БЫТЬ УЖЕ АВТОРИЗИРОВАН
        # ─────────────────────────────────────────────────────
        
        try:
            profile_button = page.locator('[data-marker="user-profile-button"]')
            if await profile_button.is_visible(timeout=2000):
                logger.success(account_id, "Already authenticated!")
                return True
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # 3. ИЩЕМ КНОПКУ ВХОДА
        # ─────────────────────────────────────────────────────
        
        login_button = None
        
        # Вариант 1: Кнопка "Войти"
        try:
            login_button = page.locator("button:has-text('Войти')").first
            if await login_button.is_visible(timeout=2000):
                await login_button.click()
                await asyncio.sleep(1)
                logger.info(account_id, "Clicked login button (variant 1)")
        except Exception:
            pass
        
        # Вариант 2: Кнопка "Мобильный номер"
        if not login_button:
            try:
                phone_btn = page.locator("button:has-text('Мобильный номер')").first
                if await phone_btn.is_visible(timeout=2000):
                    await phone_btn.click()
                    await asyncio.sleep(1)
                    logger.info(account_id, "Clicked phone button (variant 2)")
            except Exception:
                pass
        
        # Вариант 3: Input поле телефона
        try:
            phone_input = page.locator('input[type="tel"]').first
            if await phone_input.is_visible(timeout=2000):
                await phone_input.click()
                await asyncio.sleep(0.5)
                await phone_input.fill("")
                await asyncio.sleep(0.3)
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # 4. ВВОДИМ НОМЕР ТЕЛЕФОНА
        # ─────────────────────────────────────────────────────
        
        phone_input = page.locator('input[type="tel"]').first
        
        for attempt in range(3):
            try:
                if await phone_input.is_visible(timeout=2000):
                    await phone_input.click()
                    await asyncio.sleep(0.3)
                    
                    # Очищаем
                    await phone_input.press("Control+A")
                    await asyncio.sleep(0.1)
                    await phone_input.press("Delete")
                    await asyncio.sleep(0.2)
                    
                    # Печатаем номер
                    await phone_input.type(phone, delay=50)
                    await asyncio.sleep(0.5)
                    
                    logger.info(account_id, f"Entered phone: {phone}")
                    break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.warning(account_id, f"Failed to enter phone: {e}")
                    return False
        
        # ─────────────────────────────────────────────────────
        # 5. НАЖИМАЕМ КНОПКУ "ОТПРАВИТЬ КОД"
        # ─────────────────────────────────────────────────────
        
        send_code_button = None
        
        # Вариант 1: "Отправить код"
        try:
            send_code_button = page.locator("button:has-text('Отправить код')").first
            if await send_code_button.is_visible(timeout=3000):
                await send_code_button.click()
                await asyncio.sleep(2)
                logger.info(account_id, "Clicked 'Send code' button")
        except Exception:
            pass
        
        # Вариант 2: "Продолжить"
        if not send_code_button:
            try:
                continue_btn = page.locator("button:has-text('Продолжить')").first
                if await continue_btn.is_visible(timeout=3000):
                    await continue_btn.click()
                    await asyncio.sleep(2)
                    logger.info(account_id, "Clicked 'Continue' button")
            except Exception:
                pass
        
        # ─────────────────────────────────────────────────────
        # 6. ЖДЁМ ВВОДА КОДА (может быть автоматический)
        # ─────────────────────────────────────────────────────
        
        print(f"\n  {Fore.CYAN}╔═══════════════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}                                                       {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  📱 SMS КОД ОЖИДАЕТСЯ                                {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  Avito может автоматически заполнить код            {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  Или введите вручную в браузере                     {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  Ожидание: {timeout} секунд                              {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}                                                       {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}╚═══════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        if notifier:
            try:
                msg = f"""
📱 *ТРЕБУЕТСЯ SMS КОД*

📍 Аккаунт: `{account_id}`
📞 Телефон: {phone}

Код отправлен на телефон.
Введите код в браузере или он будет заполнен автоматически.

⏳ Ожидание: {timeout} сек
"""
                await notifier.send_message(msg, parse_mode="Markdown")
            except Exception:
                pass
        
        # ─────────────────────────────────────────────────────
        # 7. ЖДЁМ ЗАПОЛНЕНИЯ КОДА (АВТОМАТИЧЕСКИ ИЛИ ВРУЧНУЮ)
        # ─────────────────────────────────────────────────────
        
        # Ищем поле кода и ждём его заполнения
        start_time = asyncio.get_event_loop().time()
        code_filled = False
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Проверяем наличие кода в любом из возможных полей
                code_input = page.locator('input[type="text"]').first
                
                if await code_input.is_visible(timeout=1000):
                    code_value = await code_input.input_value()
                    
                    # Если код заполнен (4+ символа)
                    if code_value and len(code_value) >= 4:
                        logger.success(account_id, f"Code detected: {code_value}")
                        code_filled = True
                        break
                
                # Проверяем, авторизирован ли уже
                profile_button = page.locator('[data-marker="user-profile-button"]')
                if await profile_button.is_visible(timeout=500):
                    logger.success(account_id, "Already authorized!")
                    code_filled = True
                    break
                
                await asyncio.sleep(1)
            
            except Exception:
                await asyncio.sleep(1)
        
        # ─────────────────────────────────────────────────────
        # 8. ПРОВЕРЯЕМ АВТОРИЗАЦИЮ
        # ─────────────────────────────────────────────────────
        
        await asyncio.sleep(2)
        
        # Попытка 1: Проверяем кнопку профиля
        try:
            profile_button = page.locator('[data-marker="user-profile-button"]')
            if await profile_button.is_visible(timeout=3000):
                logger.success(account_id, "Login successful!")
                return True
        except Exception:
            pass
        
        # Попытка 2: Проверяем URL
        current_url = page.url
        if "profile" in current_url and "login" not in current_url:
            logger.success(account_id, "Login successful (URL check)!")
            return True
        
        # Попытка 3: Проверяем имя пользователя
        try:
            user_name = page.locator('[data-marker="user-name"]')
            if await user_name.is_visible(timeout=2000):
                logger.success(account_id, "Login successful (name check)!")
                return True
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # 9. ЕСЛИ КОД НЕ БЫЛ ЗАПОЛНЕН
        # ─────────────────────────────────────────────────────
        
        if not code_filled:
            print(f"\n  {Fore.YELLOW}⏱️ Таймаут! Код не был заполнен за {timeout} секунд{Style.RESET_ALL}")
            logger.warning(account_id, "Code not filled in time")
            return False
        
        logger.warning(account_id, "Authorization failed")
        return False
    
    except Exception as e:
        logger.error(account_id, f"SMS login error: {e}", severity="HIGH")
        return False