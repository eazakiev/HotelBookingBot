from motor import motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

from tgbot.config import load_config

config = load_config(".env")
db_user = config.db.user
db_pass = config.db.password

client = motor_asyncio.AsyncIOMotorClient(f'mongodb+srv://{db_user}:{db_pass}@hotels.drwoz57.mongodb.net/'
                                          '?retryWrites=true&w=majority')


def get_history_collection() -> AsyncIOMotorCollection:
    """ Возвращает асинхронную коллекцию истории пользователей из MongoDB """
    db = client['Hotels']
    return db['History']
