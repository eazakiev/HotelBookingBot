from aiogram.dispatcher.filters.state import StatesGroup, State


class SelectCity(StatesGroup):
    """ States city """
    wait_city_name = State()
    select_city = State()


class SelectDates(StatesGroup):
    """ States dates """
    start_select_date_in = State()
    select_date_in = State()
    start_select_date_out = State()
    select_date_out = State()
    is_date_correct = State()


class GetHotels(StatesGroup):
    """ States hotels """
    is_info_correct = State()
    get_hotels_menu = State()


class BestDeal(StatesGroup):
    """ States bestdeal """
    select_price_range = State()
    wait_min_price = State()
    wait_max_price = State()
    select_distance_range = State()
    wait_min_distance = State()
    wait_max_distance = State()


class History(StatesGroup):
    """ State history """
    show_history = State()
