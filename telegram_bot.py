# telegram_bot.py

from telethon import TelegramClient

def run_telegram_bot(api_id, api_hash, bot_token):
    """
    Подключается к Telegram через Telethon как бот и выводит имя бота.
    """
    async def _main():
        client = TelegramClient("bot_session", api_id, api_hash)
        await client.start(bot_token=bot_token)
        me = await client.get_me()
        print("Telegram бот успешно подключился!")
        print("Бот зарегистрирован как:", me.username)
        await client.disconnect()

    import asyncio
    asyncio.run(_main())
