from asyncio.exceptions import TimeoutError
from datetime import date
from typing import Union

from aiohttp import ClientSession, ClientTimeout, ServerTimeoutError

from tgbot.keyboards.inline import create_cities_markup, create_hotel_keyboard
from tgbot.misc.named_tuples import CitiesMessage, HotelInfo, HotelMessage
from tgbot.misc.named_tuples import ID
from tgbot.misc.rapidapi_exceptions import ResponseIsEmptyError
from tgbot.misc.rapidapi_keys import get_headers_by_correct_rapidapi_key, change_rapid_api_key


async def find_cities(city: str) -> dict:
    """
    Анализирует ответ json, чтобы получить cities dict.
    Возвращает dict, где ключами являются названия городов, а значениями - идентификаторы городов
    """
    cities_dict: dict = await trying_to_get_cities_dict(city=city)
    if cities_dict.get('error') is not None:
        return cities_dict
    city_suggestions: list = cities_dict.get('suggestions')
    city_entities: list = city_suggestions[0]['entities']
    if not city_entities:
        return {'error': 'cities_not_found'}
    cities_with_id = dict()
    for city_dict in city_entities:
        name, city_id = city_dict.get('name'), city_dict.get('destinationId')
        cities_with_id[name] = city_id
    return cities_with_id


async def request_to_api(url: str, querystring: dict) -> dict:
    """ Базовая функция, которая отправляет запрос в rapidapi с помощью методов aiohttp """
    timeout = ClientTimeout(total=10)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.get(url=url,
                                   headers=get_headers_by_correct_rapidapi_key(),
                                   params=querystring) as response:
                if response.ok:
                    response_json = await response.json()
                    return response_json
                if response.status == 429:
                    change_rapid_api_key()
    except ServerTimeoutError:
        return {'error': 'timeout'}
    except TimeoutError:
        return {'error': 'timeout'}


async def trying_to_get_cities_dict(city: str) -> dict:
    """ Пытается получить dict с городами 3 раза, если результат не найден, возвращает dict с ошибкой """
    attempts = 0
    while attempts < 3:
        try:
            cities_dict: dict = await get_cities_json(city=city)
            attempts += 1
            if isinstance(cities_dict, dict):
                return cities_dict
        except ResponseIsEmptyError:
            return {'error': 'empty'}
    return {'error': 'empty'}


async def get_cities_json(city: str) -> dict:
    """
    Отправляет поисковый запрос в rapidapi
    по названию выбранного города. Возвращает json найденных городов
    """
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": city, "locale": "ru_RU", "currency": "RUB"}
    cities_json = await request_to_api(url=url, querystring=querystring)
    if cities_json is None:
        raise ResponseIsEmptyError
    return cities_json


async def get_hotels_json(destination_id: str, date_in: date, date_out: date, sort_by: str, page: int) -> dict:
    """
    Отправляет поисковый запрос в rapidapi
    по выбранному идентификатору города. Возвращает json найденных отелей
    """
    url = "https://hotels4.p.rapidapi.com/properties/list"
    querystring = {"destinationId": destination_id, "pageNumber": str(page), "pageSize": "25",
                   "checkIn": str(date_in), "checkOut": str(date_out), "adults1": "1",
                   "sortOrder": sort_by, "locale": "en_US",
                   "currency": "USD", 'landmarkIds': 'City center'}
    hotels_json = await request_to_api(url=url, querystring=querystring)
    if hotels_json is None:
        raise ResponseIsEmptyError
    return hotels_json


async def get_bestdeal_hotels_json(destination_id: str, date_in: date, date_out: date, page: int,
                                   min_price: int, max_price: int) -> dict:
    """
    Отправляет поисковый запрос с пользовательскими параметрами в rapidapi
    по выбранному идентификатору города. Возвращает json найденных отелей
    """
    url = "https://hotels4.p.rapidapi.com/properties/list"
    querystring = {"destinationId": destination_id, "pageNumber": str(page), "pageSize": "25",
                   "checkIn": str(date_in), "checkOut": str(date_out), "adults1": "1",
                   "priceMin": str(min_price), "priceMax": str(max_price), "sortOrder": "DISTANCE_FROM_LANDMARK",
                   "locale": "en_US", "currency": "USD", "landmarkIds": "City center"}
    hotels_json = await request_to_api(url=url, querystring=querystring)
    if hotels_json is None:
        raise ResponseIsEmptyError
    return hotels_json


async def get_hotel_photos_json(hotel_id: ID) -> dict:
    """
    Отправляет запрос на поиск в rapidapi по выбранному идентификатору отеля.
    Возвращает json найденных фотографий
    """
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {"id": str(hotel_id)}
    photos_json = await request_to_api(url=url, querystring=querystring)
    if photos_json is None:
        raise ResponseIsEmptyError
    return photos_json


async def create_cities_message(city: str) -> Union[CitiesMessage, dict]:
    """
    Создает сообщение о найденных городах.
    Возвращает текст сообщения и встроенные кнопки с городами
    """
    found = await find_cities(city=city)
    if found.get('error') is not None:
        return found
    if len(found) == 1:
        text = f'<b>Искать в городе {"".join(city for city in found)}?</b>'
    else:
        text = '↘️ <b>Пожалуйста, уточните город</b>'
    buttons = create_cities_markup(cities_dict=found)
    return CitiesMessage(message=text, buttons=buttons)


def create_hotel_message(hotel_info: HotelInfo) -> HotelMessage:
    """
    Создает сообщение из информации об отеле. Возвращает фотографию отеля,
    подпись и встроенные кнопки с действиями для отеля
    """
    text = f'<b>{hotel_info.name}</b>\n' \
           f'{get_stars_string(hotel_info)}' \
           f'\tАдрес: {hotel_info.address}\n' \
           f'\tРасстояние до центра: {hotel_info.distance_from_center} км\n' \
           f'\tСтоимость: {hotel_info.total_cost} $\n' \
           f'\tСтоимость за ночь: {hotel_info.cost_by_night} $\n'
    buttons = create_hotel_keyboard(info=hotel_info)
    return HotelMessage(text, hotel_info.photo, buttons)


def get_stars_string(hotel_info: HotelInfo) -> str:
    """ Возвращает строку со звездочками эмодзи по количеству звезд отеля """
    if hotel_info.stars < 1:
        return ''
    return f'\t{"⭐️" * hotel_info.stars}\n'
