from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import CallbackQuery

from tgbot.database.client import get_history_collection
from tgbot.database.history import get_my_history, SandedHistory, get_found_hotels_of_command
from tgbot.keyboards.inline import generate_history_page_keyboard, create_history_page_close_keyboard, \
    create_history_page_show_keyboard
from tgbot.keyboards.reply import create_history_menu
from tgbot.misc.errors import finish_with_error
from tgbot.misc.named_tuples import HistoryPage, HotelMessage
from tgbot.misc.states import History
from tgbot.rapidapi.parse_responses import trying_to_send_with_photo


async def show_history(message: types.Message, state: FSMContext):
    """ Отправляет пользователю его историю по команде 'history' """
    await History.show_history.set()
    user_history: list[HistoryPage] = await get_my_history(message=message)
    if not user_history:
        await finish_with_error(message=message, error='history_empty')
        return
    history_to_delete: SandedHistory = await send_history_pages(message, user_history)
    await state.update_data(history_to_delete=history_to_delete)


async def show_history_text(message: types.Message, state: FSMContext):
    """ Отправляет пользователю его историю по тексту '📁 История поиска' """
    await show_history(message=message, state=state)


async def send_history_pages(message: types.Message, history: list[HistoryPage]) -> SandedHistory:
    """ Отправляет страницы истории пользователю """
    history_caption = await message.answer(text='<b>История поиска:</b>', reply_markup=create_history_menu())
    sanded_history = SandedHistory(history_caption=history_caption)
    for history_page in history:
        keyboard = await generate_history_page_keyboard(user_id=message.chat.id,
                                                        command_call_time=history_page.command_call_time)
        command_call_info = await message.answer(text=history_page.text, reply_markup=keyboard)
        sanded_history.add_new_command_message(command_call_info)

    return sanded_history


async def show_hotels_of_command(call: CallbackQuery, state: FSMContext):
    """ Отправляет пользователю отели с выбранной страницы истории """
    command_call_time = call.data.lstrip('show_history_page')
    await call.message.edit_reply_markup(create_history_page_close_keyboard(command_call_time))
    found_hotels: list[HotelMessage] = await get_found_hotels_of_command(user_id=call.message.chat.id,
                                                                         call_time=command_call_time)
    state_data = await state.get_data()
    sanded_history_messages: SandedHistory = state_data.get('history_to_delete')
    for hotel_message in found_hotels:
        message_with_hotel = await trying_to_send_with_photo(message_from_user=call.message,
                                                             hotel_message=hotel_message)
        sanded_history_messages.add_new_found_hotel(command_cal_time=command_call_time, hotel=message_with_hotel)

    await state.update_data(history_to_delete=sanded_history_messages)


async def close_hotels_of_command(call: CallbackQuery, state: FSMContext):
    """ Удаляет сообщения отелей с выбранной страницы истории """
    command_call_time = call.data.lstrip('close_history_page')
    await call.message.edit_reply_markup(create_history_page_show_keyboard(command_call_time=command_call_time))
    state_data = await state.get_data()
    sanded_history_messages: SandedHistory = state_data.get('history_to_delete')
    await sanded_history_messages.hide_found_hotels(command_cal_time=command_call_time)
    await state.update_data(history_to_delete=sanded_history_messages)


async def clear_user_history(message: types.Message, state: FSMContext):
    """ Очистить всю историю пользователей """
    state_data = await state.get_data()
    history_to_delete: SandedHistory = state_data.get('history_to_delete')
    await clear_history(user_id=message.chat.id)
    await history_to_delete.delete_all_history_messages()
    await finish_with_error(message=message, error='history_empty')


async def clear_history(user_id: int):
    """ Очистить всю историю пользователей в БД """
    collection = get_history_collection()
    await collection.update_one({'_id': user_id}, {'$set': {'history': {}}})


def register_history(dp: Dispatcher):
    dp.register_message_handler(show_history, Command('history'), state='*')
    dp.register_message_handler(show_history_text, Text('📁 История поиска'), state='*')
    dp.register_callback_query_handler(show_hotels_of_command, Text(startswith='show_history_page'),
                                       state=History.show_history)
    dp.register_callback_query_handler(close_hotels_of_command, Text(startswith='close_history_page'),
                                       state=History.show_history)
    dp.register_message_handler(clear_user_history, Text('❌ Очистить историю'), state=History.show_history)
