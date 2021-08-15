"""
Define the Telegram bot version of WebsiteWatcher
"""

import json
import logging
from configuration import Configuration
from restaurant_watch import RestaurantWatch, RestaurantWatchlist

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
        for watcher in self.watchlist.get_watchers():
            online, name, url = get_restaurant_status(watcher.slug)
            watcher.times_checked += 1
            logging.debug(f'Query for {watcher.chat_id}: {name} is {"Online" if online else "Offline"}')
            if online:
                message = f"✅ {name} is online! Get your food from {url}"
                context.bot.send_message(chat_id=watcher.chat_id, text=message)
                self.watchlist.remove(watcher.chat_id)
                continue
            
            if not watcher.is_muted:
                message = f"❌ {name} is still offline 😞"
                context.bot.send_message(chat_id=watcher.chat_id, text=message)

            if watcher.times_checked > self.runs_before_giving_up:
                message = f"⌛ {name} was offline for too long, giving up.\n\n"
                message += "If you want, you can run me again."
                context.bot.send_message(chat_id=watcher.chat_id, text=message)
                self.watchlist.remove(watcher.chat_id)
        logging.info('Done with watchlist')

    def say_hello(self, update, context):
        """ Introduce yourself """
        logging.debug(f'Got /start command from chat id {update.message.chat_id}')

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Hey! To start, send me a link to an offline wolt restaurant!"
        )

    def handle_multiple_restaurants(self, update, results):
        options = []

        logging.info(results)

        for restaurant in results:
            logging.info(restaurant)
            options.append(
                InlineKeyboardButton(restaurant['address'], callback_data=restaurant['slug'])
            )
        
        markup = InlineKeyboardMarkup([options])
        update.message.reply_text('Choose Venue:', reply_markup=markup)
    
    def handle_choice(self, update, context):
        query = update.callback_query
        query.answer()

        slug = query.data
        restaurant_names = find_restaurant(slug, True)
        if len(restaurant_names) == 0:
            context.bot.send_message(
                chat_id=message_chat_id,
                text=f"No such restaurant found :("
            )
            return

        if len(restaurant_names) != 1:
            return self.handle_multiple_restaurants(update, restaurant_names)

        message_chat_id = update.callback_query.message.chat.id

        context.bot.send_message(
            chat_id=message_chat_id,
            text=f"Let's go! I will now check {restaurant_names[0]['name']} every {self.tick_frequency} seconds."
        )

        logging.debug(f'Added {slug} to watchlist')
        watch = RestaurantWatch(message_chat_id, slug)
        self.watchlist.add(watch)

    def free_text(self, update, context):
        logging.info(f'Chat id: {update.message.chat_id}')
        text = update.message.text
        if not text.startswith('https://wolt.com/'):
            context.bot.send_message(chat_id=update.message.chat_id, text='Please send a link to a restaurant!')
            return

        slug = text.split('/')[-1]
        logging.info(f'Got slug: {slug}')
        restaurant_names = find_restaurant(slug)

        if len(restaurant_names) == 0:
            context.bot.send_message(
                chat_id=message_chat_id,
                text=f"No such restaurant found :("
            )
            return

        if len(restaurant_names) != 1:
            return self.handle_multiple_restaurants(update, restaurant_names)

        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Let's go! I will now check {restaurant_names[0]['name']} every {self.tick_frequency} seconds."
        )

        logging.debug(f'Added {slug} to watchlist')
        watch = RestaurantWatch(update.message.chat_id, slug)
        self.watchlist.add(watch)

    def unmute(self, update, context):
        users_watcher = self.watchlist.get_watcher(update.message.chat_id)
        if users_watcher:
            users_watcher.is_muted = False
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Unmuted! I will now let you know on each check if the restaurant is offline or online!"
            )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="You need to set a watch first!"
            )

    def mute(self, update, context):
        users_watcher = self.watchlist.get_watcher(update.message.chat_id)
        if users_watcher:
            users_watcher.is_muted = True
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Muted! I will only text you when the restaurant is online!"
            )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="You need to set a watch first!"
            )    
    
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
        updater.dispatcher.add_handler(CommandHandler('mute', self.mute, pass_job_queue=True))
        updater.dispatcher.add_handler(CommandHandler('unmute', self.unmute, pass_job_queue=True))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, self.free_text, pass_job_queue=True))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.handle_choice))

        updater.job_queue.run_repeating(self.run_watch, self.tick_frequency)
        self.updater = updater