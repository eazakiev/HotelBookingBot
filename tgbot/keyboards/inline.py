from datetime import datetime
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot_calendar import DetailedTelegramCalendar
from telegram_bot_pagination import InlineKeyboardPaginator

from tgbot.database.client import get_history_collection
from tgbot.misc.named_tuples import HotelInfo, CalendarMarkupAndStep, Degrees


def create_cities_markup(cities_dict: dict) -> InlineKeyboardMarkup:
    """ Создает клавиатуру городов из dict с информацией о городах """
    cities_markup = InlineKeyboardMarkup()
    city_index = 1
    for city_name, city_id in cities_dict.items():
        city_button = InlineKeyboardButton(text=f'{city_index}. {city_name}', callback_data=f'search_in_city{city_id}')
        cities_markup.row(city_button)
        city_index += 1
    return cities_markup


def create_hotel_keyboard(info: HotelInfo) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру отеля с кнопками next:
    - Бронирование отеля
    - Показать на картах
    - Получить фотографии
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    hotel_id = info.hotel_id
    booking_button = InlineKeyboardButton('✅ Забронировать', url=f'hotels.com/ho{hotel_id}')
    latitude, longitude = info.coordinates
    maps_button = InlineKeyboardButton('🌍 На карте', callback_data=f'get_hotel_map{latitude}/{longitude}')
    photos_button = InlineKeyboardButton('📷 Фото', callback_data=f'get_hotel_photos{hotel_id}')
    keyboard.add(booking_button, maps_button, photos_button)
    return keyboard


CUSTOM_STEPS = {'y': 'год', 'm': 'месяц', 'd': 'день'}


class CustomCalendar(DetailedTelegramCalendar):
    """ Клавиатура календаря с удобным интерфейсом """
    next_button = '➡️'
    prev_button = '⬅️'

    def __init__(self, min_date=datetime.now().date()):
        super().__init__(locale='ru', min_date=min_date)


def create_calendar(minimal_date: Optional[datetime] = None) -> CalendarMarkupAndStep:
    """ Создает календарь и получает шаг ввода """
    if minimal_date is None:
        calendar, step = CustomCalendar().build()
    else:
        calendar, step = CustomCalendar(min_date=minimal_date).build()
    return CalendarMarkupAndStep(calendar=calendar, date_type=CUSTOM_STEPS[step])


def is_correct_markup(text_before_correct: str):
    """ Используется для аналогичных клавиатур. С ответами "да"/"нет """
    is_correct = InlineKeyboardMarkup()
    yes_button = InlineKeyboardButton('Да', callback_data=f'{text_before_correct}_correct')
    no_button = InlineKeyboardButton('Нет', callback_data=f'{text_before_correct}_incorrect')
    is_correct.row(yes_button, no_button)
    return is_correct


def price_range_keyboard():
    """ Создает встроенную клавиатуру для выбора ценового диапазона """
    keyboard = InlineKeyboardMarkup(row_width=1)
    min_price_button = InlineKeyboardButton('➖ Указать от скольки', callback_data='select_min_price')
    max_price_button = InlineKeyboardButton('➕ Указать до скольки', callback_data='select_max_price')
    complete_button = InlineKeyboardButton('✅ Готово', callback_data='end_price_range')
    keyboard.add(min_price_button, max_price_button, complete_button)
    return keyboard


def distance_range_keyboard():
    """ Создает встроенную клавиатуру для выбора расстояния """
    keyboard = InlineKeyboardMarkup(row_width=1)
    max_distance_button = InlineKeyboardButton('➕ Указать расстояние', callback_data='select_max_distance')
    complete_button = InlineKeyboardButton('✅ Готово', callback_data='end_distance_range')
    keyboard.add(max_distance_button, complete_button)
    return keyboard


def inline_markup_from_dict() -> InlineKeyboardMarkup:  # dictionary: dict
    """ Преобразует клавиатурный dict во встроенную разметку"""
    keyboard = InlineKeyboardMarkup()
    return keyboard


def create_map_keyboard(latitude: Degrees, longitude: Degrees) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру карты с кнопками next:
    - Показать на картах Google
    - Показать на Картах Яндекс
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    gmaps_link = f'http://maps.google.com/maps?q={latitude},{longitude}'
    ymaps_link = f'http://maps.yandex.ru/?text={latitude},{longitude}'
    google_maps_button = InlineKeyboardButton(text='Открыть в Google Maps', url=gmaps_link)
    yandex_maps_button = InlineKeyboardButton(text='Открыть в Яндекс Картах', url=ymaps_link)
    close_message_button = InlineKeyboardButton(text='➖ Закрыть', callback_data='close_message')
    keyboard.add(google_maps_button, yandex_maps_button, close_message_button)
    return keyboard


def create_photos_keyboard(photos_amount: int, page: int = 1) -> InlineKeyboardMarkup:
    """ Создает клавиатуру пагинатора по текущей странице """
    paginator = InlineKeyboardPaginator(photos_amount, current_page=page, data_pattern='get_photo{page}')
    paginator.add_after(InlineKeyboardButton(text='➖ Закрыть', callback_data='close_message'))
    return paginator.markup


async def generate_history_page_keyboard(user_id: int, command_call_time: str) -> Optional[InlineKeyboardMarkup]:
    """ Создает встроенную клавиатуру с кнопкой отображения истории, если отели были найдены вызванной командой """
    is_hotels = await is_hotels_were_found(user_id, command_call_time)
    if not is_hotels:
        return None
    keyboard = InlineKeyboardMarkup()
    show_hotels_button = InlineKeyboardButton('⬇️ Показать найденные отели',
                                              callback_data=f'show_history_page{command_call_time}')
    keyboard.row(show_hotels_button)
    return keyboard


async def is_hotels_were_found(user_id, call_time: str) -> bool:
    """ Проверяет, были ли найдены отели после вызова команды """
    collection = get_history_collection()
    user: dict = await collection.find_one({'_id': user_id})
    history = user['history']
    found_hotels = history[call_time]['found_hotels']
    return True if found_hotels else False


def create_history_page_close_keyboard(command_call_time: str) -> InlineKeyboardMarkup:
    """ Создает клавиатуру с кнопкой закрытия истории """
    keyboard = InlineKeyboardMarkup()
    close_hotels_button = InlineKeyboardButton('➖ Скрыть найденные отели',
                                               callback_data=f'close_history_page{command_call_time}')
    keyboard.row(close_hotels_button)
    return keyboard


def create_history_page_show_keyboard(command_call_time: str) -> InlineKeyboardMarkup:
    """ Создает клавиатуру с кнопкой отображения истории """
    keyboard = InlineKeyboardMarkup()
    show_hotels_button = InlineKeyboardButton('⬇️ Показать найденные отели',
                                              callback_data=f'show_history_page{command_call_time}')
    keyboard.row(show_hotels_button)
    return keyboard
