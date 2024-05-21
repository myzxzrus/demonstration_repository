from .tools.audit import RedisSession

rs = RedisSession()


def get_redis():
    yield rs
