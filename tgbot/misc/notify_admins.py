from aiogram import Bot

from tgbot.config import load_config

config = load_config(".env")
db_user = config.db.user
db_pass = config.db.password


async def set_startup_notify(bot: Bot):
    """ Отправляет пользователям с правами админа уведомление о запуске бота """
    for admin in config.tg_bot.admin_ids:
        await bot.send_message(admin, text="Бот Запущен и готов к работе!")
