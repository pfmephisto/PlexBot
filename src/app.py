import logging
from telegram_bot import start_bot

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - \
                        %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.debug('Loading enviroment variables')

start_bot()
