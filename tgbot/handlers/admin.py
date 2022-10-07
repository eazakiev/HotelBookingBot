from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from tgbot.keyboards.reply import start


async def admin_start(message: types.Message):
    """ Запуск бота с правами администратора """
    await message.answer(f'❓<b>Выберите действие</b>', reply_markup=start)


async def go_to_main_menu(message: types.Message, state: FSMContext):
    """ Завершает сценарий. Возврат в главное меню """
    await go_home(message=message, state=state)


async def go_home(message: types.Message, state: FSMContext):
    """ Завершает сценарий. Возврат в главное меню """
    await state.finish()
    await admin_start(message)


def register_admin(dp: Dispatcher):
    """ Функция регистрации хендлеров """
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
    dp.register_message_handler(go_to_main_menu, text='🏠 Главное меню', state='*')
