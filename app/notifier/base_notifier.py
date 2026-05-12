class BaseNotifier:
    def send(self, title, message):
        raise NotImplementedError