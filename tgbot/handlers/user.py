from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tgbot.keyboards.reply import start


async def user_start(message: Message):
    """ Запуск бота с правами пользователя """
    await message.answer(f'❓<b>Выберите действие</b>', reply_markup=start)


async def go_to_main_menu(message: types.Message, state: FSMContext):
    """ Завершает сценарий. Возврат в главное меню """
    await go_home(message=message, state=state)


async def go_home(message: types.Message, state: FSMContext):
    """ Завершает сценарий. Возврат в главное меню """
    await state.finish()
    await user_start(message)


def register_user(dp: Dispatcher):
    """ Функция регистрации хендлеров """
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(go_to_main_menu, text='🏠 Главное меню', state='*')
