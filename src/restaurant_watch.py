"""
Define a restaurant watch list    
"""

class RestaurantWatch:
    def __init__(self, chat_id: str, slug: str):
        self.chat_id = chat_id
        self.slug = slug
        self.times_checked = 0

class RestaurantWatchlist:
    def __init__(self):
        self.__watchers = dict()

    def add(self, watch: RestaurantWatch):
        self.__watchers[watch.chat_id] = watch

    def get_watchers(self):
        return [watch for watch in self.__watchers.values()]

    def remove(self, chat_id: str):
        self.__watchers.pop(chat_id)