"""
Define the Configuration class
"""
import json
import logging

class InvalidConfiguration(Exception):
    """ Indicate that the configuration is invalid """
    pass

class Configuration:
    # Poor man's enum
    TELEGRAM: str = 'telegram'
    TWILIO: str = 'twilio'

    """ Parse configuration from the file and represent the config as an object """
    def __init__(self, config_path: str):
        """Read the configuration from the file and deserialize it

        Args:
            config_path (str): The path for config.json
        """
        logging.debug(f'Reading the configuration from {config_path}')
        with open(config_path, 'rb') as config_file:
            raw_json = config_file.read()
        self.__config = json.loads(raw_json)
        self.from_config = lambda key: self.__config.get(key, None)
        
        # Read the common parts of the configuration
        self.watchers_list = self.from_config('watchers')

        # Make sure that exactly one mode is enabled
        if not (self.from_config('mode')['telegram'] ^ self.from_config('mode')['twilio']):
            raise InvalidConfiguration('Zero or two modes enabled! Pick one!')

        # Read the relevant parts of the configuration per the mode we're in
        if self.from_config('mode')['telegram']:
            self.mode = Configuration.TELEGRAM
            self.read_telegram_config()
        else:
            self.mode = Configuration.TWILIO
            self.read_twilio_config()
        

    def read_telegram_config(self):
        """ In case we are running in Telegram mode
        """
        self.token = self.from_config('telegram_config').get('token')
        self.password = self.from_config('telegram_config').get('password')
        self.tick_frequency = self.from_config('telegram_config').get('tick_frequency')


    def read_twilio_config(self):
        """ In case we are running in Twilio mode
        """
        self.sid = self.from_config('twilio_config').get('sid')
        self.auth = self.from_config('twilio_config').get('auth')
        self.receiver_number = self.from_config('twilio_config').get('receiver_number')
        self.caller_number = self.from_config('twilio_config').get('caller_number')
        self.tick_frequency = self.from_config('twilio_config').get('tick_frequency')
        self.debug_mode = self.from_config('twilio_config').get('debug_mode')