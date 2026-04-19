from gateway.observer import Observer

class BaseHandler(Observer):
    def update(self, topic: str, payload: str):
        raise NotImplementedError()