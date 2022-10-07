from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="ℹ️ Справка")
        ],
        [
            KeyboardButton(text="⬇️ Недорогие отели"),
            KeyboardButton(text="⬆️ Дорогие отели")
        ],
        [
            KeyboardButton(text="🔍 Поиск с параметрами")
        ],
        [
            KeyboardButton(text="📁 История поиска")
        ]
    ]

)


def show_more_hotels_keyboard() -> ReplyKeyboardMarkup:
    """ Создает клавиатуру разметки ответа, которая отображается с отелями """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    show_more_button = KeyboardButton('➕ Показать еще')
    go_home_button = KeyboardButton('🏠 Главное меню')
    keyboard.add(show_more_button, go_home_button)
    return keyboard


def create_history_menu():
    """ Создает клавиатуру ответа при отображении истории пользователя """
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    clear_history_button = KeyboardButton('❌ Очистить историю')
    go_home_button = KeyboardButton('🏠 Главное меню')
    keyboard.add(clear_history_button, go_home_button)
    return keyboard
