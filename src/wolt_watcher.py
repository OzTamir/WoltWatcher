"""
WoltWatcher.py - A Telegram bot that monitors Wolt restaurant and notifies when they can take orders again.
Author: OzTamir
URL: https://github.com/OzTamir/WoltWatcher
"""

import json
import logging
from configuration import Configuration
from watcher.watcher_manager import WatcherManager
from twilio_mode import TwilioWatcher
from telegram_bot import Bot

logging.basicConfig(
    level=logging.INFO,
    format='[WoltWatcher][%(levelname)s][%(filename)s:%(funcName)s]: %(message)s')
CONFIG_FILE = 'config.json'

def start_bot(watcher: WatcherManager, config: Configuration):
    """Run the telegram bot

    Args:
        watcher (WatcherManager): A WatcherManager object, used to manage the watching of urls
        config (Configuration): A python representation of the config file on the disk
    """
    bot = Bot(watcher, config.token, config.password, config.tick_frequency)
    bot.run_bot()

def main():
    logging.info('Starting...')
    # Setup the configuration and the WatcherManager
    config = Configuration(CONFIG_FILE)
    watcher_manager = WatcherManager(config.watchers_list)

    # Run in the configured mode
    return start_bot(watcher_manager, config)

if __name__ == '__main__':
    main()