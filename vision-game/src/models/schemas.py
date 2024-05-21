from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel


class BaseResponseSchema(BaseModel):
    msg: str
    status: Union[str] = None



# {'access_token': access_token, 'token_type': 'bearer', 'user': user, 'role': 'string'}