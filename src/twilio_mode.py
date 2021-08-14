"""
Implement the watcher loop with calling capabilities
"""
import time
import logging

from twilio.rest import Client
from twilio.twiml.voice_response import Pause, VoiceResponse, Say

from configuration import Configuration
from watcher.watcher_manager import WatcherManager

class TwilioWatcher:
    """ Implement a Twilio based Website Watcher """
    def __init__(self, watcher: WatcherManager, config: Configuration):
        """Initialize the Watcher

        Args:
            watcher (WatcherManager): Used to manage the watched sites
            config (Configuration): The configuration from config.json
        """
        self.manager = watcher

        # Create the Twilio API object
        self.receiver = config.receiver_number
        self.caller = config.caller_number
        self.twilio = Client(config.sid, config.auth)
        self.tick_frequency = config.tick_frequency
        self.debug_mode = config.debug_mode
    
    
    def call(self, messages: list):
        """ Make a call with a TTS made from a list of strings

        Args:
            messages (list): A list of strings to say over the phone call

        Returns:
            twilio.calls.Call: Information about the call made
        """
        number_of_calls = len(messages)
        # Just as a saftey measure - don't make a call if there aren't any messages
        if number_of_calls < 1:
            return None
        logging.info(f'Making a call with {number_of_calls} messages')
        response = VoiceResponse()
        # Wait for one second for better understanding
        response.pause(length=1)
        for message in messages:
            response.say(message)
            response.pause(length=1)
        response.say('That will be all, bye bye!')
        # If the config states that this is a debug mode, only print the content of the TTS input
        logging.debug(response)
        if self.debug_mode:
            return None
        else:
            return self.twilio.calls.create(twiml=response, to=self.receiver, from_=self.caller)


    def watch_loop(self):
        """ Run a round of WatcherManager and report changes """
        messages = []
        for watcher, change in self.manager.watch():
            # Skip the logic if there was no change
            if not change.did_change:
                logging.debug(f'{watcher.name} did not change')
                continue
            # If the page changed, but no new words - alert only if 'AlertAnyChange' was set in the watcher's config
            if len(change.new_whitelisted) == 0 and len(change.new_blacklisted) == 0:
                if watcher.alert_any_change:
                    messages.append(f"{watcher.name} changed (no new whitelisted/blacklisted words)")
            if len(change.new_whitelisted) > 0:
                new_words = ', '.join(change.new_whitelisted)
                messages.append(f"{watcher.name} changed (These words were added - {new_words})")
            # BUG: The blacklist isn't about removed words, its the same as the whitelist
            if len(change.new_blacklisted) > 0:
                new_words = ', '.join(change.new_blacklisted)
                messages.append(f"{watcher.name} changed (These words were removed - {new_words})")
        
        # Send a call with all the updates found
        if len(messages) > 0:
            self.call(messages)


    def run_watcher(self):
        """ Run the Twilio watcher """
        logging.info('Entering the Twilio while loop...')
        while True:
            logging.debug('Running a watch loop')
            try:
                self.watch_loop()
            finally:
                logging.debug(f'Sleeping for {self.tick_frequency} seconds')
                time.sleep(self.tick_frequency)
