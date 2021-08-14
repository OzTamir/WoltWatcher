"""
Define the Telegram bot version of WebsiteWatcher
"""

import logging
from configuration import Configuration
from restaurant_watch import RestaurantWatch, RestaurantWatchlist

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
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
        watchers = self.watchlist.get_watchers()
        for watcher in watchers:
            online, name, url = get_restaurant_status(watcher.slug)
            watcher.times_checked += 1
            logging.debug(f'Query for {watcher.chat_id}: {name} is {"Online" if online else "Offline"}')
            if online:
                message = f"✅ {name} is online! Get your food from {url}"
                context.bot.send_message(chat_id=watcher.chat_id, text=message)
                self.watchlist.remove(watcher.chat_id)
                continue
            
            message = f"❌ {name} is still offline 😞"
            context.bot.send_message(chat_id=watcher.chat_id, text=message)

            if watcher.times_checked > self.runs_before_giving_up:
                message = f"⌛ {name} was offline for too long, giving up.\n\n"
                message += "If you want, you can run me again."
                context.bot.send_message(chat_id=watcher.chat_id, text=message)
                self.watchlist.remove(watcher.chat_id)
        


    def start_watching(self, update, context):
        """ Start the JobQueue that ticks the watcher """
        logging.debug(f'Got /watch command from chat id {update.message.chat_id}')

        if len(context.args) != 1 or not context.args[0].startswith('https://wolt.com/'):
            context.bot.send_message(chat_id=update.message.chat_id, text='Usage: /watch {wolt_url}')
            return

        slug = context.args[0].split('/')[-1]
        restaurant_names = find_restaurant(slug)
        if len(restaurant_names) != 1:
            context.bot.send_message(chat_id=update.message.chat_id, text='Could not find restaurant :(')
            return

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Let's go! I will now check {restaurant_names[0]} every {self.tick_frequency} seconds."
        )

        logging.debug(f'Added {slug} to watchlist')
        watch = RestaurantWatch(update.message.chat_id, slug)
        self.watchlist.add(watch)

    def say_hello(self, update, context):
        """ Introduce yourself """
        logging.debug(f'Got /start command from chat id {update.message.chat_id}')

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Hey! To start, send /watch {wolt_restaurant_url}"
        )

    def free_text(self, update, context):
        text = update.message.text
        if not text.startswith('https://wolt.com/'):
            context.bot.send_message(chat_id=update.message.chat_id, text='Usage: {wolt_url}')
            return

        slug = text.split('/')[-1]
        logging.info(f'Got slug: {slug}')
        restaurant_names = find_restaurant(slug)
        if len(restaurant_names) != 1:
            context.bot.send_message(chat_id=update.message.chat_id, text='Could not find restaurant :(')
            return

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Let's go! I will now check {restaurant_names[0]} every {self.tick_frequency} seconds."
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
        self.runs_before_giving_up = config.runs_before_giving_up
        self.tick_frequency = config.tick_frequency
        self.watchlist = RestaurantWatchlist()

        updater = Updater(config.token)
        #updater.dispatcher.add_handler(CommandHandler('watch', self.start_watching, pass_job_queue=True))
        updater.dispatcher.add_handler(CommandHandler('start', self.say_hello, pass_job_queue=True))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, self.free_text, pass_job_queue=True))

        updater.job_queue.run_repeating(self.run_watch, self.tick_frequency)
        self.updater = updater