import uvicorn
import sys
from fastapi import FastAPI
from src.api import api_list
from src import Config


app = FastAPI(title='VISION-GAME', description='This is a project of a game for training vision at your computer.', version='0.0.1')


class Routers:
    def __init__(self, app, routers: list):
        self.app = app
        self.routers = routers

    def apply_routers(self):
        for rout in self.routers:
            self.app.include_router(rout)
        return self.app


routers = Routers(app, api_list)
app = routers.apply_routers()


if __name__ == '__main__':
    res = sys.argv
    if len(res) > 1 and res[1] == 'home':
        uvicorn.run('app:app', host=Config.home['host'], port=Config.home['port'], log_level='info')
    elif len(res) > 1 and res[1] == 'work':
        uvicorn.run('app:app', host=Config.work['host'], port=Config.work['port'], log_level='info')
    else:
        uvicorn.run('app:app', host='0.0.0.0', port=5000, log_level='info')