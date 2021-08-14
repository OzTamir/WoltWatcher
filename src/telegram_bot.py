"""
Define the Telegram bot version of WebsiteWatcher
"""

import logging

from telegram.ext import Updater, CommandHandler
from watcher.watcher_manager import WatcherManager

class Bot:
    """ A Telegram Bot to watch and alert for URL changes """
    def watch_tick(self, context):
        """Run a round of WatcherManager and report any changes

        Args:
            self (Bot): The bot class
            context (telegram.ext.callbackcontext.CallbackContext): Object used for interaction with Telegram
        """
        for watcher, change in self.manager.watch():
            # Skip the logic if there was no change
            if not change.did_change:
                logging.debug(f'{watcher.url} did not change')
                continue
            # If the page changed, but no new words - alert only if 'AlertAnyChange' was set in the watcher's config
            if len(change.new_whitelisted) == 0 and len(change.new_blacklisted) == 0:
                if watcher.alert_any_change:
                    message = f"🔄 {watcher.url} changed (no new whitelisted/blacklisted words)"
                    context.bot.send_message(chat_id=context.job.context, text=message)
            if len(change.new_whitelisted) > 0:
                new_words = ', '.join(change.new_whitelisted)
                message = f"🆕 {watcher.url} changed (These words were added - {new_words})"
                context.bot.send_message(chat_id=context.job.context, text=message)
            # BUG: The blacklist isn't about removed words, its the same as the whitelist
            if len(change.new_blacklisted) > 0:
                new_words = ', '.join(change.new_blacklisted)
                message = f"❌ {watcher.url} changed (These words were removed - {new_words})"
                context.bot.send_message(chat_id=context.job.context, text=message)


    def start_watching(self, update, context):
        """ Start the JobQueue that ticks the watcher """
        logging.debug(f'Got /watch command from chat id {update.message.chat_id}')
        if self.allowed_users.get(update.message.chat_id, None) is None:
            context.bot.send_message(chat_id=update.message.chat_id, text="Unauthorized user! Please use the /unlock command and supply a password.")
            return
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Let's go! I will now run every {self.tick_frequency} seconds.")
        context.job_queue.run_repeating(self.watch_tick, self.tick_frequency, context=update.message.chat_id)


    def stop_watching(self, update, context):
        """ Stop the JobQueue that ticks the watcher """
        logging.debug(f'Got /stop command from chat id {update.message.chat_id}')
        if self.allowed_users.get(update.message.chat_id, None) is None:
            context.bot.send_message(chat_id=update.message.chat_id, text="Unauthorized user! Please use the /unlock command and supply a password.")
            return
        context.bot.send_message(chat_id=update.message.chat_id, text='OK, I will stop running now.')
        context.job_queue.stop()


    def unlock(self, update, context):
        """ Allow a user to authnticate """
        logging.debug(f'Got /unlock command from chat id {update.message.chat_id}')
        if len(context.args) != 1:
            context.bot.send_message(chat_id=update.message.chat_id, text='Usage: /unlock {password}')
            return
        if self.allowed_users.get(update.message.chat_id, None) is not None:
            context.bot.send_message(chat_id=update.message.chat_id, text="Already Authenticated! Use /watch to run me.")
            return
        if context.args[0] == self.bot_password:
            self.allowed_users[update.message.chat_id] = True
            context.bot.send_message(chat_id=update.message.chat_id, text='Authenticated! Use /watch to run me.')
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text='Wrong password, please try again.')


    def lock(self, update, context):
        """ Remove a user from the authnticated users list """
        logging.debug(f'Got /lock command from chat id {update.message.chat_id}')
        if self.allowed_users.get(update.message.chat_id, None) is None:
            context.bot.send_message(chat_id=update.message.chat_id, text="Unauthorized user! Please use the /unlock command and supply a password.")
            return
        del self.allowed_users[update.message.chat_id]
        context.job_queue.stop()
        context.bot.send_message(chat_id=update.message.chat_id, text='Logged off and stopped. Bye!')


    def run_bot(self):
        """ Run the bot and wait for messages """
        self.updater.start_polling()
        logging.info('Bot started! Waiting for messages...')
        self.updater.idle()


    def __init__(self, watcher_manager: WatcherManager, telegram_token: str, password: str, tick_frequency: int=60):
        """ Initialize the bot

        Args:
            watcher_manager (WatcherManager): Object representation of the config's list of watched URLs
            telegram_token (str): The token recieved from @BotFather
            password (str): A password used to authenticate the bot's users
            tick_frequency (int, optional): What is the frequency of checking for updates. Defaults to 60.
        """
        logging.debug('Registering with Telegram...')

        self.manager = watcher_manager
        self.bot_password = password
        self.tick_frequency = tick_frequency
        self.allowed_users = dict()

        updater = Updater(telegram_token)
        updater.dispatcher.add_handler(CommandHandler('unlock', self.unlock, pass_job_queue=True))
        updater.dispatcher.add_handler(CommandHandler('lock', self.lock, pass_job_queue=True))

        updater.dispatcher.add_handler(CommandHandler('watch', self.start_watching, pass_job_queue=True))
        updater.dispatcher.add_handler(CommandHandler('stop', self.stop_watching, pass_job_queue=True))
        self.updater = updater