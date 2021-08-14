"""
Utility functions used in the Watcher codebase
"""
import logging
import hashlib
from watcher.watcher import Watcher, InvalidWatcherConfiguration

def read_watchers_from_config(watchers_list: list):
    """Parse the supplied json into a list of Watcher objects.

    Args:
        watchers_list (list): List of watcher objects from the config file

    Returns:
        list: List of the configurations as Watcher objects
    """
    logging.debug('Creating Watcher objects...')
    watcher_objects = []
    for watcher_item in watchers_list:
        try:
            watcher_objects.append(
                Watcher(watcher_item)
            )
        except InvalidWatcherConfiguration:
            logging.error(f'Invalid Configuration ({watcher_item.name})!')
    number_of_watchers = len(watcher_objects)
    logging.info(f'Created {number_of_watchers} watchers')
    return watcher_objects


def calculate_md5(html: str):
    """Calculate the MD5 of the given HTML

    Args:
        html (str): The HTML to calculate MD5 for

    Returns:
        str: The MD5 of the given HTML string
    """
    return hashlib.md5(html.encode('utf-8'))


def search_wordlist(words: list, html: str):
    """Return the words in a list that appear in the HTML

    Args:
        words (list): A list of words to look for
        html (str): The string to look for the words in

    Returns:
        list: The list of words from the list found in the HTML
    """
    return [word for word in words if word in html]