from aiogram import Bot
from aiogram.types import BotCommand


async def set_default_commands(bot: Bot):
    """ Функция, устанавливает команды по умолчанию """
    return await bot.set_my_commands(
        commands=[
            BotCommand("start", "Запустить бота"),
            BotCommand("help", "Получить справку"),
            BotCommand("lowprice", "Узнать топ самых дешёвых отелей в городе"),
            BotCommand("highprice", "Узнать топ самых дорогих отелей в городе"),
            BotCommand("bestdeal", "Узнать топ отелей, наиболее подходящих по цене и расположению от центра"),
            BotCommand("history", "Узнать историю поиска отелей")
        ],

    )
