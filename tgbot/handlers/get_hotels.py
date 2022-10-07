import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import ReplyKeyboardRemove, CallbackQuery, Message

from tgbot.database.history import add_command_to_history, add_city_to_history
from tgbot.keyboards.inline import price_range_keyboard, distance_range_keyboard, create_calendar, CustomCalendar, \
    CUSTOM_STEPS, is_correct_markup
from tgbot.misc.dates import get_readable_date
from tgbot.misc.errors import is_message_error, finish_with_error, delete_errors_messages
from tgbot.misc.named_tuples import KM
from tgbot.misc.states import SelectCity, SelectDates, BestDeal, GetHotels
from tgbot.rapidapi.hotels_request import create_cities_message

time_offset = datetime.timezone(datetime.timedelta(hours=3))


async def define_commands(message: types.Message, state: FSMContext):
    """
    Улавливает команды отелей с низкими ценами, высокими ценами и отелей с наилучшими предложениями.
    Запрашивает у пользователя название города
    """
    command = message.text.lstrip('/')
    await message.answer("<b>↘️ Введите город, в котором будет производится поиск отелей</b>",
                         reply_markup=ReplyKeyboardRemove())
    await SelectCity.wait_city_name.set()
    await register_command_in_db(command, message, state)


async def show_lowprice(message: types.Message, state: FSMContext):
    """ Ловит текст об отелях с низкими ценами. Запрашивает у пользователя название города """
    command = 'lowprice'
    await message.answer("<b>↘️ Введите город, в котором будет производится поиск отелей</b>",
                         reply_markup=ReplyKeyboardRemove())
    await SelectCity.wait_city_name.set()
    await register_command_in_db(command, message, state)


async def show_highprice(message: types.Message, state: FSMContext):
    """ Ловит текст о дорогих отелях. Запрашивает у пользователя название города """
    command = 'highprice'
    await message.answer("<b>↘️ Введите город, в котором будет производится поиск отелей</b>",
                         reply_markup=ReplyKeyboardRemove())
    await SelectCity.wait_city_name.set()
    await register_command_in_db(command, message, state)


async def show_bestdeal(message: types.Message, state: FSMContext):
    """ Ловит текст об отелях с лучшими предложениями. Запрашивает у пользователя название города """
    command = 'bestdeal'
    await message.answer("<b>↘️ Введите город, в котором будет производится поиск отелей</b>",
                         reply_markup=ReplyKeyboardRemove())
    await SelectCity.wait_city_name.set()
    await register_command_in_db(command, message, state)


async def get_cities_by_name(message: types.Message, state: FSMContext):
    """
    Принимает название города от пользователя, и получает запрос к rapidapi по имени. Если города найдены,
    бот отправляет сообщение со встроенными кнопками для выбора правильного города
    """
    city = message.text
    await state.update_data(city_name=city)
    await add_city_name_to_db(city_name=city, state=state)
    search = await message.answer('<i>Выполняю поиск...</i>')
    cities_message = await create_cities_message(city)
    await message.chat.delete_message(search.message_id)
    if is_message_error(cities_message):
        await finish_with_error(message=message, error=cities_message.get('error'))
    else:
        text, buttons = cities_message
        await message.answer(text, reply_markup=buttons)

        await SelectCity.select_city.set()


async def set_city_id(call: CallbackQuery, state: FSMContext):
    """ Получает идентификатор города (destination id) из обратного вызова. Начинает выбирать даты """
    city_id = call.data.lstrip('search_in_city')
    await state.update_data(city_id=city_id)
    await call.answer('Город выбран', show_alert=False)
    await call.message.edit_text('<b>🏙 Город выбран!</b>', reply_markup=None)
    state_data = await state.get_data()
    command = state_data.get('command_type')

    if command == 'bestdeal':
        await start_select_price_range(call, state=state)
        return
    await SelectDates.start_select_date_in.set()
    await start_select_date_in(call=call)


async def start_select_price_range(call: CallbackQuery, state: FSMContext):
    """ Запускает процесс выбора цены """
    await state.update_data(min_price=None, max_price=None)
    await BestDeal.select_price_range.set()
    await call.message.answer('<b>Укажите диапазон цены за ночь</b>', reply_markup=price_range_keyboard())


async def send_min_price_request(call: CallbackQuery, state: FSMContext):
    """ Запрашивает у пользователя минимальную цену за ночь """
    await call.message.edit_reply_markup(reply_markup=None)
    message = await call.message.answer('<b>Отправьте минимальную цену в $</b>\n'
                                        'Пример: <b>100</b> или <b>50</b>')
    await state.update_data(message_to_delete=message)
    await state.update_data(errors_messages=[])
    await state.update_data(message_to_edit=call.message)

    await BestDeal.wait_min_price.set()


async def get_min_price(message: types.Message, state: FSMContext):
    """ Получает минимальную цену и проверяет ее """
    state_data = await state.get_data()
    errors: list[Message] = state_data.get('errors_messages')
    try:
        price = int(message.text)
    except ValueError:
        error_message = await message.answer('<b>❗️Отправьте боту число!</b>')
        errors.extend([error_message, message])
        await state.update_data(errors_messages=errors)
        return
    max_price = state_data.get('max_price')
    if max_price is not None:
        if max_price < price:
            error_message = await message.answer('<b>❗️Минимальная стоимость должна быть меньше максимальной!</b>')
            errors.extend([error_message, message])
            await state.update_data(errors_messages=errors)
            return
    message_from_bot: Message = state_data.get('message_to_delete')
    message_from_user: Message = message
    message_with_select_price: Message = state_data.get('message_to_edit')
    await message_from_bot.delete()
    await message_from_user.delete()

    await state.update_data(min_price=price)
    await delete_errors_messages(message_list=errors)
    await state.update_data(errors_messages=[])
    await edit_price_message(message_to_edit=message_with_select_price, state=state)
    await BestDeal.select_price_range.set()


async def send_max_price_request(call: CallbackQuery, state: FSMContext):
    """ Запрашивает у пользователя максимальную цену за ночь """
    await call.message.edit_reply_markup(reply_markup=None)
    message = await call.message.answer('<b>Отправьте максимальную цену в $</b>\n'
                                        'Пример: <b>100</b> или <b>50</b>')
    await state.update_data(message_to_delete=message)
    await state.update_data(message_to_edit=call.message)
    await BestDeal.wait_max_price.set()


async def get_max_price(message: Message, state: FSMContext):
    """ Получает максимальную цену и проверяет ее """
    state_data = await state.get_data()
    errors: list[Message] = state_data.get('errors_messages')
    try:
        price = int(message.text)
    except ValueError:
        error_message = await message.answer('<b>Отправьте боту число!</b>')
        errors.extend([error_message, message])
        await state.update_data(errors_messages=errors)
        return
    min_price = state_data.get('min_price')
    if min_price is not None:
        if min_price > price:
            error_message = await message.answer('<b>❗️Максимальная стоимость должна быть больше минимальной!</b>')
            errors.extend([error_message, message])
            await state.update_data(errors_messages=errors)
            return
    message_from_bot: Message = state_data.get('message_to_delete')
    message_from_user: Message = message
    message_with_select_price: Message = state_data.get('message_to_edit')
    await message_from_bot.delete()
    await message_from_user.delete()

    await state.update_data(max_price=price)
    await delete_errors_messages(message_list=errors)
    await state.update_data(errors_messages=[])
    await edit_price_message(message_to_edit=message_with_select_price, state=state)
    await BestDeal.select_price_range.set()


async def edit_price_message(message_to_edit: Message, state: FSMContext):
    """ Редактирует сообщение с информацией о ценовом диапазоне """
    state_data = await state.get_data()
    min_price, max_price = state_data.get('min_price'), state_data.get('max_price')
    if max_price is None:
        text = f'<b>Укажите диапазон цены за ночь</b>\n' \
               f'Минимальная цена: <b>{min_price} $</b>'
    elif min_price is None:
        text = f'<b>Укажите диапазон цены за ночь</b>\n' \
               f'Максимальная цена: <b>{max_price} $</b>'
    else:
        text = f'<b>Укажите диапазон цены за ночь</b>\n' \
               f'Минимальная цена: <b>{min_price} $</b>\n' \
               f'Максимальная цена: <b>{max_price} $</b>'

    await message_to_edit.edit_text(text=text, reply_markup=price_range_keyboard())


async def end_price_range_selecting(call: CallbackQuery, state: FSMContext):
    """ Завершает процесс выбора цены """
    state_data = await state.get_data()
    if state_data.get('min_price') is None and state_data.get('max_price') is None:
        await state.update_data(min_price=1, max_price=5000000)
    elif state_data.get('min_price') is None:
        await state.update_data(min_price=1)
    elif state_data.get('max_price') is None:
        await state.update_data(max_price=5000000)
    await call.message.edit_text('<b>💲 Диапазон цен выбран!</b>')
    await start_select_distance_range(call, state)


async def start_select_distance_range(call, state):
    """ Запускает процесс выбора расстояния """
    await state.update_data(max_distance=None)
    await BestDeal.select_distance_range.set()
    await call.message.answer('<b>Укажите максимальную удаленность от центра</b>',
                              reply_markup=distance_range_keyboard())


async def send_max_distance_request(call: CallbackQuery, state: FSMContext):
    """ Запрашивает у пользователя максимальное расстояние от центра """
    await call.message.edit_reply_markup(reply_markup=None)
    message = await call.message.answer('<b>Отправьте максимальную удаленность от центра в Км</b>\n'
                                        'Пример: <b>5</b> или <b>10</b>')
    await state.update_data(message_to_delete=message)
    await state.update_data(errors_messages=[])
    await state.update_data(message_to_edit=call.message)
    await BestDeal.wait_max_distance.set()


async def get_max_distance(message: Message, state: FSMContext):
    """ Получает максимальное расстояние и проверяет его """
    state_data = await state.get_data()
    errors: list[Message] = state_data.get('errors_messages')
    try:
        distance: KM = float(message.text)
    except ValueError:
        error_message = await message.answer('<b>❗️Отправьте боту число!</b>')
        errors.extend([error_message, message])
        await state.update_data(errors_messages=errors)
        return
    message_from_bot: Message = state_data.get('message_to_delete')
    message_from_user: Message = message
    message_with_select_distance: Message = state_data.get('message_to_edit')
    await message_from_bot.delete()
    await message_from_user.delete()

    await state.update_data(max_distance=distance)
    await delete_errors_messages(message_list=errors)
    await state.update_data(errors_messages=[])
    await edit_distance_message(message_to_edit=message_with_select_distance, state=state)
    await BestDeal.select_distance_range.set()


async def edit_distance_message(message_to_edit: Message, state: FSMContext):
    """ Редактирует сообщение с информацией о максимальном расстоянии """
    state_data = await state.get_data()
    max_distance = state_data.get('max_distance')
    text = f'<b>Укажите максимальную удаленность от центра</b>\n' \
           f'Максимальное расстояние: <b>{max_distance} Км</b>'
    await message_to_edit.edit_text(text=text, reply_markup=distance_range_keyboard())


async def end_distance_range_selecting(call: CallbackQuery, state: FSMContext):
    """ Завершает процесс выбора расстояния """
    state_data = await state.get_data()
    if state_data.get('max_distance') is None:
        await state.update_data(max_distance=1000)
    await call.message.edit_text('<b>🏠 Диапазон расстояния выбран!</b>')
    await SelectDates.start_select_date_in.set()
    await start_select_date_in(call=call)


async def start_select_date_in(call: CallbackQuery):
    """ Запускает процесс выбора даты заезда """
    calendar_info = create_calendar()
    await call.message.answer(f'↘️ <b>Укажите {calendar_info.date_type} заезда</b>',
                              reply_markup=calendar_info.calendar)
    await SelectDates.select_date_in.set()


async def select_date_in(call: CallbackQuery, state: FSMContext):
    """ Процесс выбора даты заезда """
    result, keyboard, step = CustomCalendar().process(call_data=call.data)
    if not result and keyboard:
        await call.message.edit_text(f'↘️ <b>Укажите {CUSTOM_STEPS[step]} заезда</b>',
                                     reply_markup=keyboard)
    elif result:
        await state.update_data(date_in=result)
        message = get_readable_date(str_date=str(result))
        await call.message.edit_text(f'📅 <b>Выбрано: {message}\n'
                                     f'Все верно?</b>', reply_markup=is_correct_markup('date_in'))
        await SelectDates.is_date_correct.set()


async def start_select_date_out(call: CallbackQuery, date_in: datetime):
    """ Запускает процесс выбора даты выезда """
    calendar_info = create_calendar(minimal_date=date_in)
    await call.message.answer(f'↘️ <b>Укажите {calendar_info.date_type} выезда</b>',
                              reply_markup=calendar_info.calendar)
    await SelectDates.select_date_out.set()


async def select_date_out(call: CallbackQuery, state: FSMContext):
    """ Процесс выбора даты выезда """
    state_data = await state.get_data()
    date_in = state_data.get('date_in')
    result, keyboard, step = CustomCalendar(min_date=date_in).process(call_data=call.data)
    if not result and keyboard:
        await call.message.edit_text(f'↘️ <b>Укажите {CUSTOM_STEPS[step]} выезда</b>',
                                     reply_markup=keyboard)
    elif result:
        await state.update_data(date_out=result)
        message = get_readable_date(str_date=str(result))
        await call.message.edit_text(f'📅 <b>Выбрано: {message}\n'
                                     f'Все верно?</b>', reply_markup=is_correct_markup('date_out'))
        await SelectDates.is_date_correct.set()


async def send_confirmation_date(call: CallbackQuery, state: FSMContext):
    """
    Получает ответ от пользователя о действительности выбранной даты.
    Запрашивает пользователя о достоверности всей полученной информации
    """
    state_data = await state.get_data()
    city = state_data.get('city_name')
    date_in = state_data.get('date_in')
    date_out = state_data.get('date_out')

    if call.data == 'date_in_incorrect':
        await call.answer('Попробуйте еще раз', show_alert=True)
        await call.message.delete()
        await SelectDates.start_select_date_in.set()
        await start_select_date_in(call=call)

    if call.data == 'date_out_incorrect':
        await call.answer('Попробуйте еще раз', show_alert=True)
        await call.message.delete()
        await SelectDates.start_select_date_out.set()
        await start_select_date_out(call=call, date_in=date_in)

    if call.data == 'date_in_correct':
        await call.answer('Укажите дату выезда', show_alert=False)
        await call.message.delete()
        await SelectDates.start_select_date_out.set()
        await start_select_date_out(call=call, date_in=date_in)

    if call.data == 'date_out_correct':
        await call.answer('Дата выезда указана', show_alert=False)
        await call.message.delete()
        await call.message.answer('📅 <b> Дата выбрана!</b>')
        await call.message.answer(f'❓ <b>Город: </b>{city}\n'
                                  f'<b>Дата заезда: </b>{get_readable_date(str(date_in))}\n'
                                  f'<b>Дата выезда: </b>{get_readable_date(str(date_out))}\n'
                                  f'\n'
                                  f'<b>Все верно?</b>', reply_markup=is_correct_markup('city_info'))
        await GetHotels.is_info_correct.set()


async def register_command_in_db(command: str, message: Message, state: FSMContext):
    """ Добавляет вызываемую команду в базу данных """
    call_time = datetime.datetime.now(time_offset)
    await add_command_to_history(command=command, call_time=call_time, message=message)
    await state.update_data(command_type=command, command_call_time=call_time)


async def add_city_name_to_db(city_name: str, state: FSMContext):
    """ Добавляет название выбранного города на страницу истории в базе данных """
    state_data = await state.get_data()
    call_time = str(state_data.get('command_call_time'))
    await add_city_to_history(city=city_name, call_time=call_time, user_id=state.chat)


def register_hotels(dp: Dispatcher):
    dp.register_message_handler(define_commands, Command(['lowprice', 'highprice', 'bestdeal']), state='*')
    dp.register_message_handler(show_lowprice, Text('⬇️ Недорогие отели'), state='*')
    dp.register_message_handler(show_highprice, Text('⬆️ Дорогие отели'), state='*')
    dp.register_message_handler(show_bestdeal, Text('🔍 Поиск с параметрами'), state='*')
    dp.register_message_handler(get_cities_by_name, state=SelectCity.wait_city_name)
    dp.register_callback_query_handler(set_city_id, Text(startswith='search_in_city'), state=SelectCity.select_city)
    dp.register_callback_query_handler(send_min_price_request, Text(startswith='select_min_price'),
                                       state=BestDeal.select_price_range)
    dp.register_message_handler(get_min_price, state=BestDeal.wait_min_price)
    dp.register_callback_query_handler(send_max_price_request, Text(startswith='select_max_price'),
                                       state=BestDeal.select_price_range)
    dp.register_message_handler(get_max_price, state=BestDeal.wait_max_price)
    dp.register_callback_query_handler(end_price_range_selecting, Text(startswith='end_price_range'),
                                       state=BestDeal.select_price_range)
    dp.register_callback_query_handler(send_max_distance_request, Text(startswith='select_max_distance'),
                                       state=BestDeal.select_distance_range)
    dp.register_message_handler(get_max_distance, state=BestDeal.wait_max_distance)
    dp.register_callback_query_handler(end_distance_range_selecting, Text(startswith='end_distance_range'),
                                       state=BestDeal.select_distance_range)
    dp.register_callback_query_handler(select_date_in, state=SelectDates.select_date_in)
    dp.register_callback_query_handler(select_date_out, state=SelectDates.select_date_out)
    dp.register_callback_query_handler(send_confirmation_date, state=SelectDates.is_date_correct)
