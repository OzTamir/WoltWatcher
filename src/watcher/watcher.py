"""
Define the Watcher class
"""
import requests

class InvalidWatcherConfiguration(Exception):
    """ Indicate that the configuration given to the watcher is invalid """
    pass

class Watcher:
    """ Hold information about a watcher """
    def __init__(self, watcher_item: dict):
        """Initiate a watcher object from the config file.

        Args:
            watcher_item (dict): A dictionary from the JSON array in config.json

        Raises:
            InvalidWatcherConfiguration: If the configuration is incomplete.
        """        
        try:
            self.name = watcher_item['Name'] 
            self.url = watcher_item['URL']
            self.whitelist = watcher_item['Whitelist']
            self.blacklist = watcher_item['Blacklist']
            self.alert_any_change = watcher_item['AlertAnyChange']
            self.md5 = None
            self.previous_whitelisted = []
            self.previous_blacklisted = []
        except KeyError as exception:
            invalid_key = exception.args[0]
            raise InvalidWatcherConfiguration(
                f'Invalid configuration! Key {invalid_key} was not supplied!'
            )    


    def get_html(self):
        """Get the current HTML from the web

        Returns:
            str: The HTML retrived from the given URL
        """      
        return requests.get(self.url).text

    
    def set_hash(self, new_hash: str):
        """Set the last known hash to a new value

        Args:
            new_hash (str): the updated hash
        """
        self.md5 = new_hash


    def __hash__(self):
        """Get the last known hash of the site's HTML

        Returns:
            str: The last calculated hash
        """        
        return self.md5