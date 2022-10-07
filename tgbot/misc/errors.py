from typing import Union

from aiogram.types.message import Message


def is_message_error(message) -> bool:
    """ Проверяет, является ли функция возвращенным словарем с ошибкой """
    if isinstance(message, dict):
        return True
    return False


def create_error_message(error_text: str) -> str:
    """ Создает сообщение об ошибке с помощью текстовой ошибки из возвращенного словаря """
    template = '❗️<b>{}</b>'
    if error_text == 'cities_not_found':
        return template.format('Городов с таким названием не найдено')
    if error_text == 'hotels_not_found':
        return template.format('Отелей с заданными условиями не найдено')
    if error_text == 'history_empty':
        return template.format('История пуста')
    if error_text == 'empty':
        return template.format('Произошла ошибка при получении информации о городах. Попробуйте еще раз')
    if error_text == 'timeout':
        return template.format('Произошла ошибка на сервере. Попробуйте еще раз')
    if error_text == 'page_index':
        return template.format('Найденные отели закончились')
    if error_text == 'bad_result':
        return template.format('Возникла ошибка при получении информации. Попробуйте еще раз')


async def finish_with_error(message: Message, error: str, to_delete: Union[tuple[Message, Message], Message] = None):
    """ Отправляет пользователю сообщение об ошибке и завершает сценарий """
    await message.answer(text=create_error_message(error))
    if isinstance(to_delete, Message):
        await to_delete.delete()


async def delete_errors_messages(message_list: list[Message]):
    """ Удаляет сообщения с ошибками, когда пользователь выбирает что-то в сценарии наилучшего предложения """
    if message_list is None:
        return
    for message in message_list:
        await message.delete()
