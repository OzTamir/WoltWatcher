"""
Define the Configuration class
"""
import json
import logging

class InvalidConfiguration(Exception):
    """ Indicate that the configuration is invalid """
    pass

class Configuration:
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
        
        self.token = self.from_config('telegram_config').get('token')
        self.password = self.from_config('telegram_config').get('password')
        self.tick_frequency = self.from_config('telegram_config').get('tick_frequency')