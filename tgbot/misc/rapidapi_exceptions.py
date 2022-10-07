class ResponseIsEmptyError(BaseException):
    """ Запрос к rapid api ничего не возвращает """

    def __str__(self):
        return 'Server returned None'


class PageIndexError(IndexError):
    """ Пытается вывести страницу отелей с индексом за пределы диапазона """

    def __str__(self):
        return 'Index of hotel page is out of range'


class BadRapidapiResultError(BaseException):
    """ Параметр запроса "результат" не в порядке """

    def __str__(self):
        return 'Request parameter "result" is not OK'


class HotelsNotFoundError(BaseException):
    """ Список результатов пуст """

    def __str__(self):
        return 'Results list is empty'
