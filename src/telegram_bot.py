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

    def handle_single_restaurant(self, context, chat_id, restaurant):
        if restaurant['online']:
            message = f"✅ {restaurant['name']} is online! Get your food from {restaurant['url']}"
            context.bot.send_message(chat_id=chat_id, text=message)
            return

        message = text=f"Let's go! I will now check {restaurant['name']} every {self.tick_frequency} seconds.\n"
        message += f"In the meantime, checkout the menu at {restaurant['url']}"

        context.bot.send_message(chat_id, message)

        watch = RestaurantWatch(chat_id, restaurant['slug'])
        self.watchlist.add(watch)

    def handle_multiple_restaurants(self, update, results, field_name='name'):
        options = []
        for restaurant in results:
            options.append(
                InlineKeyboardButton(restaurant[field_name], callback_data=restaurant['slug'])
            )
        
        markup = InlineKeyboardMarkup([options])
        update.message.reply_text('Choose Venue:', reply_markup=markup)
    
    def handle_find_restaurants_results(self, update, context, chat_id, find_results):
        if len(find_results) == 0:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"No such restaurant found :("
            )
            return

        if len(find_results) != 1:
            return self.handle_multiple_restaurants(update, find_results, 'address')

        restaurant = find_results[0]
        self.handle_single_restaurant(context, chat_id, restaurant)

    def handle_choice(self, update, context):
        query = update.callback_query
        query.answer()

        message_chat_id = update.callback_query.message.chat.id

        slug = query.data
        restaurant_names = find_restaurant(slug, self.restaurant_filters, True)
        self.handle_find_restaurants_results(update, context, message_chat_id, restaurant_names)

    def free_text(self, update, context):
        try:
            text = update.message.text
            logging.warning(f'Got text: {text[:100]}')
            if not text.startswith('https://wolt.com/'):
                restaurant_names = find_restaurant(text, self.restaurant_filters, False)
            else:
                slug = text.split('/')[-1]
                restaurant_names = find_restaurant(slug, self.restaurant_filters, True)

            self.handle_find_restaurants_results(update, context, update.message.chat_id, restaurant_names)
        except:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f"No such restaurant found :("
            )

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
        self.restaurant_filters = config.filters
        self.watchlist = RestaurantWatchlist()

        updater = Updater(config.token)
        updater.dispatcher.add_handler(CommandHandler('mute', self.mute, pass_job_queue=True))
        updater.dispatcher.add_handler(CommandHandler('unmute', self.unmute, pass_job_queue=True))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, self.free_text, pass_job_queue=True))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.handle_choice))

        updater.job_queue.run_repeating(self.run_watch, self.tick_frequency)
        self.updater = updater