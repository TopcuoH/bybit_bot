import os
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

LOG_FILE = "bybit_log.txt"

# 👤 Названия субаккаунтов по UID (заполни как нужно)
SUBACCOUNT_NAMES = {
    "455762817": "Account7",
    "455762662": "Account6",
    "455762521": "Account5",
    "455762367": "Account4",
    "454226016": "Account1",
    "450150066": "Account2",
    "404635218": "Account3"
}

def log(message, to_console=True):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")
    if to_console:
        print(full_message)

def get_timestamp():
    return int(time.time() * 1000)

def create_signature(secret, timestamp, api_key, recv_window, query_string=""):
    payload = f"{timestamp}{api_key}{recv_window}{query_string}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def get_headers(api_key, api_secret, query_string=""):
    timestamp = get_timestamp()
    recv_window = "5000"
    signature = create_signature(api_secret, timestamp, api_key, recv_window, query_string)
    return {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-TIMESTAMP": str(timestamp),
        "X-BAPI-RECV-WINDOW": recv_window,
        "X-BAPI-SIGN": signature,
        "X-BAPI-SIGN-TYPE": "2"
    }

def query_balance(account_type="UNIFIED", member_id=None, account_name=""):
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    endpoint = os.getenv('BYBIT_ENDPOINT')

    query_params = f"accountType={account_type}&coin=USDT"
    if member_id:
        query_params += f"&memberId={member_id}"

    headers = get_headers(api_key, api_secret, query_params)
    url = f"{endpoint}/v5/asset/transfer/query-account-coins-balance?{query_params}"

    resp = requests.get(url, headers=headers)
    try:
        data = resp.json()
    except Exception as e:
        log(f"[{account_name or member_id or 'main'}] ❌ Ошибка парсинга JSON: {e}")
        log(f"Raw:\n{resp.text}")
        return

    if data.get("retCode") != 0:
        log(f"[{account_name or member_id or 'main'}] ❌ Ошибка от Bybit: {data.get('retMsg')}")
        log(f"Raw:\n{resp.text}")
        return

    result = data.get("result", {})
    coin_list = result.get("balance", [])

    log(f"\n=== Баланс аккаунта: {account_name or member_id or 'main'} ===")
    for coin in coin_list:
        coin_name = coin.get("coin")
        total = coin.get("walletBalance")
        available = coin.get("availableBalance")
        if float(total) > 0:
            log(f"Монета: {coin_name} | Всего: {total} | Доступно: {available}")

def get_subaccount_list():
    log("\n📥 Получаем список субаккаунтов...")
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    endpoint = os.getenv('BYBIT_ENDPOINT')

    query = "limit=50&page=1"
    headers = get_headers(api_key, api_secret, query)
    url = f"{endpoint}/v5/user/query-sub-members?{query}"

    resp = requests.get(url, headers=headers)
    try:
        data = resp.json()
    except Exception as e:
        log(f"Ошибка разбора списка субаккаунтов: {e}")
        log(f"Raw:\n{resp.text}")
        return []

    if data.get("retCode") != 0:
        log("Ошибка получения субаккаунтов: " + str(data.get("retMsg")))
        log(f"Raw:\n{resp.text}")
        return []

    result = []
    for sub in data["result"].get("subMembers", []):
        uid = sub["uid"]
        # ⚡ Подставляем красивое имя из словаря
        name = SUBACCOUNT_NAMES.get(str(uid), sub.get("username") or f"UID {uid}")
        result.append((uid, name))
    return result

if __name__ == "__main__":
    # Основной аккаунт
    query_balance(account_name="Основной аккаунт")

    # Субаккаунты
    subaccounts = get_subaccount_list()
    for uid, name in subaccounts:
        query_balance(member_id=uid, account_name=name)
