import os
import uuid
import redis
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from ..models import Audit
from ..api.auth.schemas import TokenData


def add_audit(session: Session, **kwargs):
    timezone_offset = +3.0  # Moscow Standard Time (UTC+03:00)
    tzinfo = timezone(timedelta(hours=timezone_offset))
    audit = Audit()
    audit.id = str(uuid.uuid4())
    audit.user = kwargs['user'] if 'user' in kwargs else None
    audit.action = kwargs['action'] if 'action' in kwargs else None
    audit.date = datetime.now(tzinfo)
    session.add(audit)


class RedisSession:
    ttl = 300
    host = 'localhost'
    port = 6379
    password = 'password'

    def __init__(self):
        if os.environ.get('FAST_ENV', "") == "production":
            self.ttl = int(os.environ['REDIS_TTL']) if os.environ['REDIS_TTL'] else self.ttl
            self.host = os.environ['REDIS_HOST'] if os.environ['REDIS_HOST'] else self.host
            self.port = int(os.environ['REDIS_PORT']) if os.environ['REDIS_PORT'] else self.port
            self.password = os.environ['REDIS_PASSWORD'] if os.environ['REDIS_PASSWORD'] else self.password
        self.redis = redis.StrictRedis(
            host=self.host,
            port=self.port,
            password=self.password
        )
    def get_session(self):
        return self.redis


class UsersMonitor:

    def __init__(self, rs: RedisSession):
        self.redis_session = rs
        self.ttl = self.redis_session.ttl
        self.redis = self.redis_session.get_session()

    def set_active_user(self, current_user: TokenData):
        try:
            key = f'users:active:{current_user.login}'
            self.redis.hset(key, mapping=current_user.dict())
            self.redis.expire(name=key, time=self.ttl)
        except:
            print('error 1')

    def get_active_users(self):
        result = []
        try:
            encoding = 'utf-8'
            key = 'users:active:*'
            lu = [str(j.decode(encoding)) for j in self.redis.scan(match=key)[1]]
            for user in lu:
                encoding = 'utf-8'
                _l = self.redis.hgetall(user)
                _ttl = self.redis.ttl(user)
                item = {}
                for _v in _l:
                    _b = _l.get(_v)
                    item[_v.decode(encoding)] = _b.decode(encoding)
                item['ttl'] = _ttl
                result.append(item)
        except:
            print('error 2')
        return result