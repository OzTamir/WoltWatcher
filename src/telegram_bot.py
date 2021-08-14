"""
Define the Telegram bot version of WebsiteWatcher
"""

import logging
from configuration import Configuration
from restaurant_watch import RestaurantWatch, RestaurantWatchlist

from telegram.ext import Updater, CommandHandler
from wolt_api import find_restaurant, get_restaurant_status

class Bot:
    """ A Telegram Bot to watch and alert for URL changes """
    def run_watch(self, context):
        """Run a round of WatcherManager and report any changes

        Args:
            self (Bot): The bot class
            context (telegram.ext.callbackcontext.CallbackContext): Object used for interaction with Telegram
        """
        logging.debug('Running watchlist check...')
        for watcher in self.watchlist:
            online, name, url = get_restaurant_status(watcher.slug)
            logging.debug(f'Query for {watcher.chat_id}: {name} is {"Online" if online else "Offline"}')
            if not online:
                message = f"❌ {name} is still offline 😞"
                context.bot.send_message(chat_id=watcher.chat_id, text=message)
                continue
            
            message = f"✅ {name} is online! Get your food from {url}"
            context.bot.send_message(chat_id=watcher.chat_id, text=message)
            self.watchlist.remove(watcher.chat_id)


    def start_watching(self, update, context):
        """ Start the JobQueue that ticks the watcher """
        logging.debug(f'Got /watch command from chat id {update.message.chat_id}')
        if self.allowed_users.get(update.message.chat_id, None) is None:
            context.bot.send_message(chat_id=update.message.chat_id, text="Unauthorized user! Please use the /unlock command and supply a password.")
            return

        if len(context.args) != 1 or not context.args[0].startswith('https://wolt.com/'):
            context.bot.send_message(chat_id=update.message.chat_id, text='Usage: /watch {wolt_url}')
            return

        slug = context.args[0].split('/')[-1]
        if len(find_restaurant(slug)) != 1:
            context.bot.send_message(chat_id=update.message.chat_id, text='Could not find restaurant :(')
            return

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Let's go! I will now check {slug} every {self.tick_frequency} seconds."
        )

        logging.debug(f'Added {slug} to watchlist')
        watch = RestaurantWatch(update.message.chat_id, slug)
        self.watchlist.add(watch)

    def run_bot(self):
        """ Run the bot and wait for messages """
        self.updater.start_polling()
        logging.info('Bot started! Waiting for messages...')
        self.updater.idle()


    def __init__(self, config: Configuration):
        """ Initialize the bot

        Args:
            config (Configuration): Contains the telegram bot's configuration
        """
        logging.debug('Registering with Telegram...')

        self.bot_password = config.password
        self.tick_frequency = config.tick_frequency
        self.allowed_users = dict()
        self.watchlist = RestaurantWatchlist()

        updater = Updater(config.token)
        updater.dispatcher.add_handler(CommandHandler('watch', self.start_watching, pass_job_queue=True))
        updater.job_queue.run_repeating(self.run_watch, self.tick_frequency)
        self.updater = updater