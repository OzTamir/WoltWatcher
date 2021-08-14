"""
WoltWatcher.py - A Telegram bot that monitors Wolt restaurant and notifies when they can take orders again.
Author: OzTamir
URL: https://github.com/OzTamir/WoltWatcher
"""

import logging
from configuration import Configuration
from telegram_bot import Bot

logging.basicConfig(
    level=logging.INFO,
    format='[WoltWatcher][%(levelname)s][%(filename)s:%(funcName)s]: %(message)s')
CONFIG_FILE = 'config.json'

def main():
    logging.info('Starting...')
    # Setup the configuration
    config = Configuration(CONFIG_FILE)

    # Run in the configured mode
    bot = Bot(config)
    bot.run_bot()

if __name__ == '__main__':
    main()