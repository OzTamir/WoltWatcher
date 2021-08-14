"""
Define a restaurant watch list    
"""

class RestaurantWatch:
    def __init__(self, chat_id: str, slug: str):
        self.chat_id = chat_id
        self.slug = slug

class RestaurantWatchlist:
    def __init__(self):
        self.__watchers = dict()

    def add(self, watch: RestaurantWatch):
        self.__watchers[watch.chat_id] = watch

    def __iter__(self):
        for restaurant in self.__watchers:
            yield restaurant

    def remove(self, chat_id: str):
        self.__watchers.pop(chat_id)