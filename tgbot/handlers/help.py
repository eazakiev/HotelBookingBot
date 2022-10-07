from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardRemove


async def bot_help(message: types.Message):
    """ Вызов стандартной команды help """
    text = ("<b>🌟Стандартные команды:</b>",
            "/start - Запустить бота",
            "/help - Получить справку\n",
            "<b>🌟Поиск отелей:</b>",
            "/lowprice - Узнать топ самых дешёвых отелей в городе",
            "/highprice - Узнать топ самых дорогих отелей в городе",
            "/bestdeal - Узнать топ отелей, наиболее подходящих по цене и расположению от центра\n",
            "<b>🌟Ваши отели:</b>",
            "/history - Узнать историю поиска отелей")

    await message.answer('\n'.join(text), reply_markup=ReplyKeyboardRemove())


def register_help(dp: Dispatcher):
    """ Функция регистрации хендлеров """
    dp.register_message_handler(bot_help, commands=["help"], state="*")
    dp.register_message_handler(bot_help, text=["ℹ️ Справка"], state='*')
