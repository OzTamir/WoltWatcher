"""
Define the WatcherManager class
"""
import logging
from watcher.watcher import Watcher
from watcher.change_event import ChangeEvent
from watcher.watcher_utils import calculate_md5, search_wordlist, read_watchers_from_config

class WatcherManager:
    """ Manage watchers """
    def __init__(self, watchers: list):
        """Initiate the manager

        Args:
            watchers (list): a list of Watcher objects
        """
        self.watchers = read_watchers_from_config(watchers)

    
    def run_watcher(self, watcher: Watcher):
        """Run a watcher and create a ChangeEvent with information about whether the site changed

        Args:
            watcher (Watcher): The watcher to check status for

        Returns:
            ChangeEvent: Information about whether the site changed
        """
        logging.info(f'Now Running Watcher for {watcher.name}')
        change = ChangeEvent()
        # Grab the HTML and calculate the MD5 for it
        new_html = watcher.get_html()
        new_md5 = calculate_md5(new_html)

        # Make sure that if it's the first run we don't alert a change
        if watcher.md5 is None:
            watcher.md5 = new_md5

        # If the page was changed since the last check
        if new_md5 != watcher.md5:
            logging.debug(f'Found new MD5! {new_md5}')
            # Get the white/black-listed words from the HTML
            whitelisted = search_wordlist(watcher.whitelist, new_html)
            blacklisted = search_wordlist(watcher.blacklist, new_html)
            
            # Set the ChangeEvent values
            change.did_change = True
            change.new_whitelisted = [word for word in whitelisted if word not in watcher.previous_whitelisted]
            change.new_blacklisted = [word for word in blacklisted if word not in watcher.previous_blacklisted]
            
            # Set the watcher values
            watcher.md5 = new_md5
            watcher.previous_whitelisted = whitelisted
            watcher.previous_blacklisted = blacklisted
        return change

    def watch(self):
        """Iterate over the watchers and watch each one

        Yields:
            ChangeEvent: Information about a given watcher
        """
        logging.debug('Running a watch iteration...')
        for watcher in self.watchers:
            yield watcher, self.run_watcher(watcher)
