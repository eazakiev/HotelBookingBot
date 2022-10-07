from datetime import date
from typing import Union

from aiogram.types import Message
from aiogram.utils.exceptions import InvalidHTTPUrlContent, WrongFileIdentifier, BadRequest

from tgbot.misc.named_tuples import HotelInfo, ID, USD, HotelMessage
from tgbot.misc.named_tuples import KM, Link
from tgbot.misc.rapidapi_exceptions import ResponseIsEmptyError, BadRapidapiResultError, HotelsNotFoundError
from tgbot.rapidapi.hotels_request import get_hotel_photos_json
from tgbot.rapidapi.hotels_request import get_hotels_json, get_bestdeal_hotels_json


async def get_hotels_info(data: dict, page: int) -> Union[list[HotelInfo], dict]:
    """ Получает необходимую информацию для запроса из данных. Функция анализа вызовов отелей """
    command = data.get('command_type')
    if command == 'bestdeal':
        hotels_dict = await get_bestdeal_hotels_dict(data=data, page=page)
    else:
        hotels_dict = await get_hotels_dict(command=command, data=data, page=page)
    if hotels_dict.get('error') is not None:
        return hotels_dict
    try:
        date_in, date_out = data.get('date_in'), data.get('date_out')
        if command == 'bestdeal':
            results = trying_to_get_bestdeal_results(hotels=hotels_dict, max_distance=data.get('max_distance'))
        else:
            results = trying_to_get_results(hotels=hotels_dict)

        return parse_hotels_info(results=results, date_in=date_in, date_out=date_out)
    except HotelsNotFoundError:
        return {'error': 'hotels_not_found'}
    except BadRapidapiResultError:
        return {'error': 'bad_result'}


async def get_bestdeal_hotels_dict(data: dict, page: int):
    """ Получает словарь отелей из rapid api с пользовательскими параметрами в запросе """
    min_price, max_price = data.get('min_price'), data.get('max_price')
    date_in, date_out = data.get('date_in'), data.get('date_out')
    try:
        hotels_dict_with_min_distance = await get_bestdeal_hotels_json(destination_id=data.get('city_id'),
                                                                       date_in=date_in, date_out=date_out, page=page,
                                                                       min_price=min_price, max_price=max_price)
        return hotels_dict_with_min_distance
    except ResponseIsEmptyError:
        return {'error': 'empty'}


async def get_hotels_dict(command: str, data: dict, page: int) -> dict:
    """ Получает информацию об отелях из rapidapi """
    sort_by = 'PRICE' if command == 'lowprice' else 'PRICE_HIGHEST_FIRST'
    date_in, date_out = data.get('date_in'), data.get('date_out')
    try:
        hotels_dict: dict = await get_hotels_json(destination_id=data.get('city_id'),
                                                  date_in=date_in, date_out=date_out,
                                                  sort_by=sort_by, page=page)
        return hotels_dict
    except ResponseIsEmptyError:
        return {'error': 'empty'}


def parse_hotels_info(results: list[dict], date_in: date, date_out: date) -> list[HotelInfo]:
    """ Анализирует найденную информацию о каждом отеле. Возвращает список информации о каждом отеле """
    hotels_info = list()
    for result in results:
        name: str = result.get('name')
        stars: int = int(result.get('starRating'))
        address_info = result.get('address')
        address: str = generate_address(info=address_info)
        hotel_id: ID = result.get('id')
        high_resolution_link: Link = trying_to_get_link(result)
        distance_to_center = result.get('landmarks')[0].get('distance')
        correct_distance: KM = distance_str_to_float_in_km(str_distance=distance_to_center)
        days_in = (date_out - date_in).days
        price_by_night: USD = result.get('ratePlan').get('price').get('exactCurrent')
        total_price: USD = days_in * price_by_night

        coordinates = (result.get('coordinate').get('lat'), result.get('coordinate').get('lon'))
        hotels_info.append(HotelInfo(
            hotel_id=hotel_id,
            name=name,
            stars=stars,
            address=address,
            distance_from_center=correct_distance,
            total_cost=round(total_price, 2),
            cost_by_night=round(price_by_night, 2),
            photo=high_resolution_link,
            coordinates=coordinates
        ))
    return hotels_info


async def get_hotel_photo_links(hotel_id: ID) -> Union[list[Link], dict]:
    """ Получает список URL-адресов фотографий отелей по идентификатору """
    try:
        hotel_photos_json: dict = await get_hotel_photos_json(hotel_id)
    except ResponseIsEmptyError:
        return {'error': 'empty'}
    if hotel_photos_json.get('error') is not None:
        return hotel_photos_json
    hotel_images = hotel_photos_json.get('hotelImages')
    if hotel_images is not None:
        photo_links = [info.get('baseUrl').replace('{size}', 'y') for info in hotel_images]
        return photo_links
    return []


async def trying_to_send_with_photo(message_from_user: Message, hotel_message: HotelMessage):
    """
    Пытается отправить сообщение об отеле с фотографией.
    Если найдено исключение, отправляет без фотографии
    """
    try:
        message = await message_from_user.bot.send_photo(chat_id=message_from_user.chat.id, photo=hotel_message.photo,
                                                         caption=hotel_message.text,
                                                         reply_markup=hotel_message.buttons)
    except InvalidHTTPUrlContent:
        message = await message_from_user.answer(text=hotel_message.text, reply_markup=hotel_message.buttons)
    except WrongFileIdentifier:
        message = await message_from_user.answer(text=hotel_message.text, reply_markup=hotel_message.buttons)
    except BadRequest:
        message = await message_from_user.answer(text=hotel_message.text, reply_markup=hotel_message.buttons)

    return message


def trying_to_get_results(hotels: dict) -> list:
    """ Пытается получить результаты из словаря с информацией об отелях """
    if hotels.get('result') == 'OK':
        search_results: dict = hotels.get('data').get('body').get('searchResults')
        results: list = search_results.get('results')
        return results
    raise BadRapidapiResultError


def trying_to_get_bestdeal_results(hotels: dict, max_distance: int) -> list:
    """ Пытается получить результаты из словаря с информацией о подходящих отелях """
    results = trying_to_get_results(hotels=hotels)
    return slice_hotels_results_by_max(results=results, max_distance=max_distance)


def slice_hotels_results_by_max(results: list, max_distance: int):
    """ Срезает объекты отелей до отеля с максимальным расстоянием """
    index = len(results) - 1
    while index >= 0:
        hotel = results[index]
        distance_to_center = hotel.get('landmarks')[0].get('distance')
        distance: KM = distance_str_to_float_in_km(str_distance=distance_to_center)
        if distance <= max_distance:
            break
        index -= 1
    if len(results[:index + 1]) == 0:
        raise HotelsNotFoundError
    return results[:index + 1]


def distance_str_to_float_in_km(str_distance: str) -> float:
    """ Преобразует расстояние строки в милях в расстояние с плавающей точкой в км """
    distance = str_distance.rstrip(' miles')
    return round(float(distance) * 1.609, 2)


def generate_address(info: dict) -> str:
    """ Создает строку адреса из информации об адресе """
    country = info.get('countryName')
    city = info.get('locality')
    address_line = info.get('streetAddress')
    return f'{address_line}, {city}, {country}'


def trying_to_get_link(result: dict) -> str:
    """ Пытается получить фотографию отеля в высоком качестве """
    try:
        photo_link: Link = result.get('optimizedThumbUrls').get('srpDesktop')
        high_resolution_link: Link = photo_link.replace('250', '1280').replace('140', '720')
        return high_resolution_link
    except AttributeError:
        return 'link_not_found'


def is_last_page(hotels: list) -> bool:
    """ Проверяет, является ли страница последней в поиске """
    return True if 0 < len(hotels) < 25 else False
