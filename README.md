# Telegram-бот для поиска отелей на сайте Hotels.com.
## Описание.
Telegram-бот предназначен для поиска отелей на сайте Hotels.com по критериям, 
задаваемым пользователями. Используется открытый API Hotels, который расположен на
сайте rapidapi.com.
Пользователь с помощью специальных команд бота может выполнить следующие
действия (получить следующую информацию):
1. Узнать топ самых дешёвых отелей в городе (команда /lowprice).
2. Узнать топ самых дорогих отелей в городе (команда /highprice).
3. Узнать топ отелей, наиболее подходящих по цене и расположению от центра
(самые дешёвые и находятся ближе всего к центру) (команда /bestdeal)
4. Узнать историю поиска отелей (команда /history)
5. Получить помощь по работе бота (команда /help)

## Установка
Клонируйте репозиторий.
Необходимо, что-бы у вас был доступ к секретным ключам вашего Telegram-бота и RapidAPI. 
Создайте файл .env в папке проекта. Занесите в этот файл значения двух ваших секретных ключей:
```
TOKEN='секретный токен вашего Telegram-бота'
RAPIDAPI_KEY='секретный ключ X-RapidAPI-Key'
```
Создайте и активируйте виртуальное окружение.
Установите зависимости в виртуальном окружении env/ :
```
pip install -r requirements.txt
```

## Запуск
Находясь в папке проекта, запустите файл main.py
```
python main.py
```