from aiogram import Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from tgbot.config import load_config
from tgbot.database.history import add_hotel_to_history
from tgbot.keyboards.inline import create_map_keyboard, create_photos_keyboard
from tgbot.keyboards.reply import show_more_hotels_keyboard
from tgbot.misc.errors import is_message_error, finish_with_error
from tgbot.misc.named_tuples import HotelInfo, HotelMessage, ID, Link
from tgbot.misc.states import GetHotels, SelectCity
from tgbot.rapidapi.hotels_request import create_hotel_message
from tgbot.rapidapi.parse_responses import trying_to_send_with_photo, get_hotels_info, is_last_page, \
    get_hotel_photo_links

config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')


async def find_hotels_if_info_correct(call: CallbackQuery, state: FSMContext):
    """
    Если пользователь подтвердил информацию об отеле, запускается поиск отелей.
    Отправляет сообщение о первом отеле иначе запрашивает у пользователя новую информацию
    """
    message = call.message
    if call.data == 'city_info_correct':
        await state.update_data(hotels_page=1)
        await send_first_hotel(message=message, state=state, page=1)
    elif call.data == 'city_info_incorrect':
        await change_info(call=call)


async def send_new_hotel(message: Message, state: FSMContext):
    """ Отправляет сообщение о другом отеле """
    state_data = await state.get_data()
    hotel_index, hotels_page = state_data.get('hotel_index'), state_data.get('hotels_page')
    hotels_info: list[HotelInfo] = state_data.get('hotels_info')
    if hotel_index == len(hotels_info):
        await send_first_hotel(message=message, state=state, page=hotels_page + 1)
        await state.update_data(hotels_page=hotels_page + 1)
        return
    hotel = hotels_info[hotel_index]
    hotel_message: HotelMessage = create_hotel_message(hotel_info=hotel)
    message_with_hotel = await trying_to_send_with_photo(message_from_user=message, hotel_message=hotel_message)
    await add_hotel_to_history(message=message_with_hotel, call_time=state_data.get('command_call_time'))
    await state.update_data(hotel_index=hotel_index + 1)


async def send_first_hotel(message: Message, state: FSMContext, page: int):
    """ Отправляет первый отель на выбранной странице. Если страницы закончились вывод заканчивается """
    await message.delete()
    search = await message.answer('<i>Выполняю поиск...</i>')
    state_data = await state.get_data()
    if state_data.get('last_page'):
        await finish_with_error(message, error='page_index')
        return
    hotels_info: list[HotelInfo] = await get_hotels_info(data=state_data, page=page)
    if is_message_error(message=hotels_info):
        error = hotels_info.get('error')
        await finish_with_error(message, error=error)
        return
    await state.update_data(hotels_info=hotels_info, hotel_index=1)
    hotel_info: HotelInfo = hotels_info[0]
    hotel_message = create_hotel_message(hotel_info)
    await message.chat.delete_message(search.message_id)
    await message.answer('<b>Найденные отели:</b>', reply_markup=show_more_hotels_keyboard())
    message_with_hotel = await trying_to_send_with_photo(message_from_user=message, hotel_message=hotel_message)
    await add_hotel_to_history(message=message_with_hotel, call_time=state_data.get('command_call_time'))
    if is_last_page(hotels_info):
        await state.update_data(last_page=True)
    await GetHotels.get_hotels_menu.set()


async def change_info(call: CallbackQuery):
    """ Отправляет пользователю запрос о новой информации для поиска """
    await call.answer('Укажите информацию заново', show_alert=True)
    await SelectCity.wait_city_name.set()
    await call.message.edit_text('<b>↘️ Введите город, в котором будет производится поиск отелей</b>')


async def get_hotel_map(call: CallbackQuery):
    """
    Отправляет геопозиция отеля на карте в качестве объекта местоположения telegram.
    Содержит две ссылки на популярные приложения для карт
    """
    latitude, longitude = map(float, call.data.lstrip('get_hotel_map').split('/'))
    await bot.send_location(chat_id=call.message.chat.id, latitude=latitude, longitude=longitude,
                            reply_markup=create_map_keyboard(latitude, longitude))


async def get_hotel_photos(call: CallbackQuery, state: FSMContext):
    """ Выполняет поиск фотографий отеля и отправляет первую из них в сообщении paginator """
    await call.answer('Выполняю поиск...')
    hotel_id: ID = int(call.data.lstrip('get_hotel_photos'))
    photo_links: list[Link] = await get_hotel_photo_links(hotel_id)
    if is_message_error(photo_links):
        await finish_with_error(call.message, error=photo_links.get('error'))
        return
    await state.update_data(photos=photo_links)
    await send_hotel_photo(message=call.message, found_photos=photo_links)


async def show_hotel_photo(call: CallbackQuery, state: FSMContext):
    """ Переходит на следующую страницу с фотографией в сообщении пагинатора """
    photo_index = int(call.data.lstrip('get_photo'))
    state_data = await state.get_data()
    photos = state_data.get('photos')
    await send_new_hotel_photo(message=call.message, found_photos=photos, photo_index=photo_index)


async def send_hotel_photo(message: Message, found_photos: list[Link]):
    """ Отправляет первую фотографию отеля """
    await bot.send_photo(chat_id=message.chat.id,
                         photo=found_photos[0],
                         reply_markup=create_photos_keyboard(len(found_photos)))


async def send_new_hotel_photo(message: Message, found_photos: list, photo_index: int = 1):
    """ Редактирует сообщение paginator с фотографией отеля по номеру страницы """
    await bot.edit_message_media(chat_id=message.chat.id,
                                 message_id=message.message_id,
                                 media=InputMediaPhoto(found_photos[photo_index - 1]),
                                 reply_markup=create_photos_keyboard(len(found_photos), page=photo_index))


async def close_message(call: CallbackQuery):
    """ Удалить сообщение. Используется для сообщений с картами или фотографиями """
    await call.message.delete()


def register_next_hotels(dp: Dispatcher):
    dp.register_callback_query_handler(find_hotels_if_info_correct, Text(startswith='city_info_'),
                                       state=GetHotels.is_info_correct)
    dp.register_message_handler(send_new_hotel, Text(equals=['➕ Показать еще']), state=GetHotels.get_hotels_menu)
    dp.register_callback_query_handler(get_hotel_map, Text(startswith='get_hotel_map'), state='*')
    dp.register_callback_query_handler(get_hotel_photos, Text(startswith='get_hotel_photos'), state='*')
    dp.register_callback_query_handler(show_hotel_photo, Text(startswith='get_photo'), state='*')
    dp.register_callback_query_handler(close_message, Text(startswith='close_message'), state='*')

