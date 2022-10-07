from aiogram import types
from aiogram.types import Message
from motor.motor_asyncio import AsyncIOMotorCollection

from tgbot.database.client import get_history_collection
from tgbot.keyboards.inline import inline_markup_from_dict
from tgbot.misc.dates import get_readable_date_time
from tgbot.misc.named_tuples import HistoryPage, HotelMessage


async def add_hotel_to_history(message: Message, call_time):
    """
    Добавляет отель в историю пользователей в базе данных.
    Добавляет на страницу истории по времени вызова команды
    """
    collection = get_history_collection()
    user = await collection.find_one({'_id': message.chat.id})
    if user:
        history = user['history']
    else:
        history = dict()
        history[str(call_time)]['found_hotels'] = list()
    current_history_page: list = history[str(call_time)]['found_hotels']
    current_history_page.append(hotel_dict_from_message(message))
    await collection.update_one({'_id': message.chat.id}, {'$set': {'history': history}})


async def add_command_to_history(command: str, call_time, message: Message):
    """ Добавляет вызванную команду в базу данных по времени, когда была вызвана команда """
    collection = get_history_collection()
    user = await collection.find_one({'_id': message.chat.id})
    if user:
        await add_new_to_history(user, collection, command, str(call_time), message)
    else:
        await create_history(collection, command, str(call_time), message)


async def add_new_to_history(user: dict, collection: AsyncIOMotorCollection, command: str, call_time: str,
                             message: Message):
    """ Добавляет команду в историю, если пользователь существует в БД """
    user_history = user['history']
    user_history_page = create_history_dict(command=command, call_time=call_time)
    user_history[call_time] = user_history_page
    await collection.update_one({'_id': message.chat.id}, {'$set': {'history': user_history}})


async def create_history(collection: AsyncIOMotorCollection, command: str, call_time: str, message: Message):
    """ Создает запись истории пользователей в базе данных. Добавляет команду в историю пользователей в БД """
    user_history_page = create_history_dict(command=command, call_time=call_time)
    await collection.insert_one({'_id': message.chat.id, 'history': {call_time: user_history_page}})


def create_history_dict(command: str, call_time: str) -> dict:
    """ Создает запись истории по команде и времени, когда команда была вызвана """
    history_dict = {
        'text': f'<b>Команда</b> /{command} вызвана\n'
                f'в {get_readable_date_time(call_time)}',
        'found_hotels': []
    }
    return history_dict


async def add_city_to_history(city: str, call_time: str, user_id: str):
    """ Добавляет название выбранного города в текст на странице истории """
    collection = get_history_collection()
    user = await collection.find_one({'_id': user_id})
    user_history: dict = user['history']
    history_page: dict = user_history[call_time]
    text_to_edit = history_page.get('text')
    text_with_city = f'Поиск в городе <b>{city}</b>\n' + text_to_edit
    history_page['text'] = text_with_city
    await collection.update_one({'_id': user_id}, {'$set': {'history': user_history}})


def is_message_contains_photo(message: Message) -> bool:
    """ Проверяет, содержит ли сообщение фото """
    return True if message.photo else False


def get_photo_id(message: Message) -> str:
    """ Получает id фотографии """
    return message.photo[-1]['file_id']


def hotel_dict_from_message(message: Message) -> dict:
    """ Преобразует сообщение об отеле в dict с информацией об отеле """
    is_message_with_photo = is_message_contains_photo(message=message)
    hotel_dict = {
        'photo_id': get_photo_id(message) if is_message_with_photo else 'link_not_found',
        'text': message.caption if is_message_with_photo else message.text,
    }
    return hotel_dict


def hotel_message_from_hotel_dict(hotel_info: dict) -> HotelMessage:
    """ Преобразует dict с информацией об отеле в сообщение об отеле """
    return HotelMessage(
        text=hotel_info.get('text'),
        photo=hotel_info.get('photo_id'),
        buttons=inline_markup_from_dict()
    )


async def get_my_history(message: types.Message) -> list[HistoryPage]:
    """
    Возвращает список всех страниц истории пользователей в БД
    по идентификатору пользователя (получает из сообщения)
    """
    user_history: dict = await find_history_in_db(user_id=message.chat.id)
    history_pages: list[HistoryPage] = parse_user_history(history=user_history)
    return history_pages


async def get_found_hotels_of_command(user_id: int, call_time: str) -> list[HotelMessage]:
    """ Возвращает список найденных отелей по вызванной команде """
    collection = get_history_collection()
    user: dict = await collection.find_one({'_id': user_id})
    history = user['history']
    found_hotels: list[dict] = history[call_time]['found_hotels']
    found_hotels_messages: list[HotelMessage] = list(map(hotel_message_from_hotel_dict, found_hotels))
    return found_hotels_messages


async def find_history_in_db(user_id: int) -> dict:
    """ Находит историю пользователей в базе данных """
    collection = get_history_collection()
    user: dict = await collection.find_one({'_id': user_id})
    if user:
        return user['history']
    return {}


def parse_user_history(history: dict) -> list[HistoryPage]:
    """ Возвращает список страниц истории пользователей по найденной истории """
    history_pages = list()
    for call_time, history_part in history.items():
        found_hotels = [hotel_message_from_hotel_dict(hotel_info) for hotel_info in history_part.get('found_hotels')]
        history_pages.append(HistoryPage(command_call_time=call_time,
                                         text=history_part.get('text'),
                                         found_hotels=found_hotels))
    return history_pages


class SandedHistory:
    """ Класс, который работает с отправленными сообщениями в историю """
    def __init__(self, history_caption: Message):
        self.history_caption: Message = history_caption
        self.command_messages: list[Message] = list()
        self.found_hotels: dict[str, list[Message]] = dict()

    def add_new_command_message(self, message: Message):
        """ Добавляет новое сообщение с информацией о команде для отправки """
        self.command_messages.append(message)

    def add_new_found_hotel(self, command_cal_time: str, hotel: Message):
        """ Добавляет сообщение об отеле на выбранную страницу истории """
        found_hotels_of_command = self.found_hotels.get(command_cal_time)
        if found_hotels_of_command is None:
            self.found_hotels[command_cal_time] = list()
            self.found_hotels[command_cal_time].append(hotel)
            return
        self.found_hotels[command_cal_time].append(hotel)

    async def hide_found_hotels(self, command_cal_time: str):
        """ Удаляет сообщения отеля с выбранной страницы истории """
        found_hotels: list[Message] = self.found_hotels[command_cal_time]
        for hotel in found_hotels:
            await hotel.delete()
        self.found_hotels[command_cal_time] = list()

    async def delete_all_history_messages(self):
        """ Удаляет все сообщения истории """
        for history_page in self.found_hotels.values():
            for hotel in history_page:
                await hotel.delete()
        for command_message in self.command_messages:
            await command_message.delete()
        await self.history_caption.delete()
