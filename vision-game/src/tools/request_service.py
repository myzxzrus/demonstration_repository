import datetime
import json

from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..session import Base


class BaseModelRequest:
    def __init__(self, session: Session, model: Base, **kwargs):
        self.request = session.query(model)
        self.model = model
        self.page = kwargs['page'] if 'page' in kwargs else None
        self.size = kwargs['size'] if 'size' in kwargs else None
        self.role = kwargs['role'] if 'role' in kwargs else None
        self.filters = self.get_filters(kwargs['filters']) if 'filters' in kwargs else None
        self.key_is_date = kwargs['key_is_date'] if 'key_is_date' in kwargs else None
        self.global_field: list = kwargs['global_field'] if 'global_field' in kwargs else None
        self.res = None
        self.count = self.request.count()

    def get_filters(self, filters):
        if type(filters) == str:
            filters_obj = json.loads(filters)
            return filters_obj

    def _apply_filter_single(self, key, value):
        if self.key_is_date is not None and self.key_is_date == key:
            start_date = datetime.datetime.strptime(value + ' 00:00:00.000000 +03:00', '%d.%m.%Y %H:%M:%S.%f %z')
            end_date = datetime.datetime.strptime(value + ' 23:59:59.999999 +03:00',
                                                  '%d.%m.%Y %H:%M:%S.%f %z')
            self.request = self.request.filter(getattr(self.model, key).between(f'{start_date}', f'{end_date}'))
        else:
            self.request = self.request.filter(getattr(self.model, key).contains(value))

    def apply_filter(self) -> object:
        if self.filters is not None and type(self.filters) == dict:
            for key, value in self.filters.items():
                if hasattr(self.model, key):
                    if type(value) == list:
                        pass
                    else:
                        self._apply_filter_single(key, value)
                q=1
                if key == 'global' and self.global_field is not None and type(self.global_field) == list:
                    query_collection = ()
                    for g_filter in self.global_field:
                        query_collection = query_collection + (getattr(self.model, g_filter).contains(value), )
                    self.request = self.request.filter(or_(*query_collection))
        if self.page is not None and self.size is not None:
            return self.request \
                .order_by(self.model.created_utc.desc()) \
                .limit(self.size) \
                .offset((self.page - 1) * self.size).all()
        else:
            return self.request \
                .order_by(self.model.created_utc.desc()).all()

    def make_response(self):
        self.res = self.apply_filter()
        if self.page is not None and self.size is not None:
            return {'count': self.count,
                    'response': self.res,
                    'page': self.page,
                    'size': self.size}
        else:
            return {'count': self.count,
                    'response': self.res}

