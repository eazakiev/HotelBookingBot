NUMBERS_TO_MONTHS = {'01': 'января', '02': 'февраля', '03': 'марта', '04': 'апреля',
                     '05': 'мая', '06': 'июня', '07': 'июля', '08': 'августа',
                     '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'}


def get_readable_date_time(str_datetime: str) -> str:
    """ Создает записанную версию даты и времени из строки объекта datetime """
    date, time_ = str_datetime.split()
    correct_time = time_.split('.')[0].split(':')[:2]
    return f'{":".join(correct_time)}, {get_readable_date(date, ending="го")}'


def get_readable_date(str_date: str, ending: str = 'е') -> str:
    """ Создает записанную версию данных из строки объекта date """
    year, month, day = str_date.split('-')
    return f'{day.lstrip("0")}-{ending} {NUMBERS_TO_MONTHS[month]} {year}-го года'
