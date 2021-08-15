"""
Define a restaurant watch list    
"""
import logging

class RestaurantWatch:
    def __init__(self, chat_id: str, slug: str):
        self.chat_id = chat_id
        self.slug = slug
        self.times_checked = 0
        self.is_muted = True

class RestaurantWatchlist:
    def __init__(self):
        self.__watchers = dict()

    def add(self, watch: RestaurantWatch):
        self.log_watcher(watch)
        self.__watchers[watch.chat_id] = watch

    def get_watchers(self):
        return [watch for watch in self.__watchers.values()]

    def get_watcher(self, chat_id: str):
        return self.__watchers.get(chat_id, None)

    def remove(self, chat_id: str):
        self.__watchers.pop(chat_id)

    def log_watcher(self, watcher):
        log_string = f'WATCHING: {watcher.slug} | {watcher.chat_id}'
        logging.warning(log_string)