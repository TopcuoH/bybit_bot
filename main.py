import os
import sys
import time
import hmac
import hashlib
import json
import asyncio
import requests
from dotenv import load_dotenv
from telethon import TelegramClient

# Загружаем переменные окружения из файла .env
load_dotenv()

def get_credentials():
    """
    Возвращает словарь с данными для подключения к Telegram и Bybit.
    Данные берутся из переменных окружения.
    """
    TELEGRAM_API_ID    = os.environ.get("TELEGRAM_API_ID")
    TELEGRAM_API_HASH  = os.environ.get("TELEGRAM_API_HASH")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    BYBIT_API_KEY      = os.environ.get("BYBIT_API_KEY")
    BYBIT_API_SECRET   = os.environ.get("BYBIT_API_SECRET")
    BYBIT_ENDPOINT     = os.environ.get("BYBIT_ENDPOINT", "https://api.bybit.com")

    missing_vars = []
    if not TELEGRAM_API_ID:
        missing_vars.append("TELEGRAM_API_ID")
    if not TELEGRAM_API_HASH:
        missing_vars.append("TELEGRAM_API_HASH")
    if not TELEGRAM_BOT_TOKEN:
        missing_vars.append("TELEGRAM_BOT_TOKEN")
    if not BYBIT_API_KEY:
        missing_vars.append("BYBIT_API_KEY")
    if not BYBIT_API_SECRET:
        missing_vars.append("BYBIT_API_SECRET")
    if missing_vars:
        raise ValueError("Отсутствуют следующие переменные окружения: " + ", ".join(missing_vars))
    
    if not (BYBIT_ENDPOINT.startswith("http://") or BYBIT_ENDPOINT.startswith("https://")):
        BYBIT_ENDPOINT = "https://" + BYBIT_ENDPOINT

    return {
        "TELEGRAM_API_ID": int(TELEGRAM_API_ID),
        "TELEGRAM_API_HASH": TELEGRAM_API_HASH,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "BYBIT_API_KEY": BYBIT_API_KEY,
        "BYBIT_API_SECRET": BYBIT_API_SECRET,
        "BYBIT_ENDPOINT": BYBIT_ENDPOINT
    }

async def test_telegram_connection(credentials):
    """
    Инициализирует Telegram-клиента через Telethon в режиме бота и выводит имя бота.
    """
    print("Инициализируем Telegram клиент для бота...")
    client = TelegramClient("bot_session", credentials["TELEGRAM_API_ID"], credentials["TELEGRAM_API_HASH"])
    await client.start(bot_token=credentials["TELEGRAM_BOT_TOKEN"])
    print("Telegram бот успешно подключился!")
    me = await client.get_me()
    print("Бот зарегистрирован как:", me.username)
    await client.disconnect()

def generate_signature(timestamp, api_key, recv_window, query_string, api_secret):
    """
    Генерирует HMAC SHA256 подпись по схеме:
        sign = HMAC_SHA256( timestamp + api_key + recv_window + query_string, api_secret )
    """
    payload = str(timestamp) + api_key + str(recv_window) + query_string
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

def get_wallet_balance(credentials):
    """
    Выполняет приватный GET запрос к Bybit API v5 для получения баланса кошелька USDT.
    Использует endpoint: /v5/account/wallet-balance с параметрами:
        accountType=UNIFIED&coin=USDT
    """
    # Устанавливаем параметры запроса.
    params = {
        "accountType": "UNIFIED",  # или "CONTRACT", в зависимости от вашего аккаунта
        "coin": "USDT"
    }
    # Формируем query string
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    endpoint = "/v5/account/wallet-balance"
    url = credentials["BYBIT_ENDPOINT"] + endpoint + "?" + query_string

    # Параметры подписи
    recv_window = 15000
    timestamp = int(time.time() * 1000)
    sign = generate_signature(timestamp, credentials["BYBIT_API_KEY"], recv_window, query_string, credentials["BYBIT_API_SECRET"])
    
    headers = {
        "X-BAPI-API-KEY": credentials["BYBIT_API_KEY"],
        "X-BAPI-TIMESTAMP": str(timestamp),
        "X-BAPI-RECV-WINDOW": str(recv_window),
        "X-BAPI-SIGN": sign,
        "X-BAPI-SIGN-TYPE": "2"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print("Bybit баланс кошелька:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print("Ошибка при выполнении запроса баланса:", e)
        print("URL запроса:", url)
        print("Headers:", headers)

async def main():
    try:
        credentials = get_credentials()
    except ValueError as e:
        print("Ошибка при загрузке переменных окружения:", e)
        sys.exit(1)
    
    await test_telegram_connection(credentials)
    get_wallet_balance(credentials)

if __name__ == "__main__":
    asyncio.run(main())
