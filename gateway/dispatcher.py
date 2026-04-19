from collections import defaultdict

#! Observer Pattern Implementation
class EventDispatcher():
    def __init__(self):
        self._observers = defaultdict(list)
    # Add new observer to the list of observers for a specific feed ID
    def register(self, feed_ID: str, observer):
        self._observers[feed_ID].append(observer)
    
    def notify(self, feed_ID: str, payload: str):
        for obs in self._observers.get(feed_ID, []):
            obs.update(feed_ID, payload)    # Call `handlers` function