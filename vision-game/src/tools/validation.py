from sqlalchemy.orm import Session
from typing import Optional
from ..models.models import Users

async def verify_email_exist(email: str, session: Session) -> Optional[Users]:
    return session.query(Users).filter(Users.email == email).scalar()

