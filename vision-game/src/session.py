from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from .config import *

SQLALCHEMY_DATABASE_URL = f'postgresql+psycopg2://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session.configure(bind=create_engine(SQLALCHEMY_DATABASE_URL, client_encoding='utf8', poolclass=NullPool))
Base = declarative_base()


def get_db():
    db = Session()
    try:
        yield db
    except:
        db.rollback()
        raise
    finally:
        db.close()



