import asyncio
import aiogram
import os

from utils.logger import logger
from app.handlers import router
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start_bot():
    """Один цикл жизни бота"""
    bot = aiogram.Bot(token=BOT_TOKEN)
    disp = aiogram.Dispatcher()
    disp.include_router(router)

    try:
        await disp.start_polling(bot, polling_timeout=60)
    finally:
        await bot.session.close()

async def main():
    """Главный перезапускающий цикл"""
    while True:
        try:
            logger.info("Бот запущен")
            await start_bot()
        except Exception as e:
            logger.critical(f"Сбой в работе бота: {e}", exc_info=True)
            logger.info("Перезапускаю бота через 5 секунд…")
            await asyncio.sleep(5)
        else:
            # если polling завершился без исключения — выйти
            logger.info("Бот остановлен вручную.")
            break

if __name__ == "__main__":
    asyncio.run(main())
