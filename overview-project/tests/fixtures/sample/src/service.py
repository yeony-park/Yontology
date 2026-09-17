LIMIT = 10


def normalize(value):
    return value.strip().lower()


class BaseService:
    def ready(self):
        return True


class UserService(BaseService):
    def create(self, name):
        return normalize(name)[:LIMIT]


def register(name):
    return normalize(name)
