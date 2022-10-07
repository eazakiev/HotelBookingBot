import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

from tgbot.config import load_config
from tgbot.filters.admin_filter import AdminFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.echo import register_echo
from tgbot.handlers.get_history import register_history
from tgbot.handlers.get_hotels import register_hotels
from tgbot.handlers.get_next_hotels import register_next_hotels
from tgbot.handlers.help import register_help
from tgbot.handlers.user import register_user
from tgbot.misc.notify_admins import set_startup_notify
from tgbot.misc.setting_commands import set_default_commands

logger = logging.getLogger(__name__)
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
bot['config'] = config


def register_all_filters(dsp):
    dsp.filters_factory.bind(AdminFilter)


def register_all_handlers(dsp):
    register_admin(dsp)
    register_user(dsp)
    register_help(dsp)
    register_hotels(dsp)
    register_next_hotels(dsp)
    register_history(dsp)

    register_echo(dsp)


async def main(dispatcher):
    dispatcher.setup_middleware(LoggingMiddleware())
    logger.info("Starting bot")
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )

    register_all_filters(dp)
    register_all_handlers(dp)

    await set_startup_notify(bot)
    await set_default_commands(bot)

    # start
    try:
        await dp.start_polling()

    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=main)
