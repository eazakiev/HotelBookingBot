from aiogram import types, Dispatcher
from aiogram.utils.markdown import hcode


async def bot_echo(message: types.Message):
    """ Эхо без состояния """
    text = [
        f"<b>Уважаемый {message.from_user.full_name}!</b>\nЭхо без состояния.",
        "Пожалуйста введите соответствующую команду.",
    ]
    await message.answer('\n'.join(text))


async def bot_echo_all(message: types.Message):
    """ Эхо с каким-либо не распознанным состоянием """
    text = [
        f"<b>Уважаемый {message.from_user.full_name}!</b>\nСообщение не распознано, бот ожидает нажатия на кнопку.\n"
        "Содержание сообщения:",
        hcode(message.text)
    ]
    await message.answer('\n'.join(text))


def register_echo(dp: Dispatcher):
    """ Функция регистрации хендлеров """
    dp.register_message_handler(bot_echo)
    dp.register_message_handler(bot_echo_all, state="*", content_types=types.ContentTypes.ANY)
