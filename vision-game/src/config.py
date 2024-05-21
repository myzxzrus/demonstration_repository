import os

APP_ENV = os.getenv('APP_ENV', 'development')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME', 'qqqqqqqq')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'qqqqqqqq')

DATABASE_HOST = os.getenv('DATABASE_HOST', 'test.ru')
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'vision-game')

SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'test@test.ru')
SMTP_EMAIL_PASSWORD = os.getenv('SMTP_EMAIL_PASSWORD', 'Qqqqqq2023!')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.test.ru')
SMTP_PORT = os.getenv('SMTP_PORT', 465)


class Config:
    db_uri = f"postgresql+psycopg2://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    home = dict(host='127.0.0.1', port=5000, dtabase_url=db_uri)
    work = dict(host='127.0.0.1', port=5000, dtabase_url=db_uri)
    base_url = '/api/v1'

