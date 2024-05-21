import uuid
import random
from typing import List

from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from ...models import GamesPlayed, Games, AllowedGames
from .schemas import PlayedCreateScheme, AllowedGameCreateScheme
from datetime import datetime
from ..auth.schemas import TokenData


class ErrorSecretKey(Exception):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return repr(self.data)


class ExpiredSecretKey(Exception):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return repr(self.data)


async def get_game_classifier(session: Session):
    return session.query(Games).all()


async def create_game_played(session: Session, body: PlayedCreateScheme):
    gp = GamesPlayed()
    gp.id = str(uuid.uuid4())
    gp.user_id = body.user_id
    gp.game_id = body.game_id
    gp.points = body.points
    session.add(gp)
    session.commit()
    return gp


async def create_game_allowed(session: Session, body: AllowedGameCreateScheme):
    users_game = session.query(AllowedGames).filter(AllowedGames.user_id == body.user_id).all()

    list_delete = []
    list_allowed_id = []
    # Удаляем записи которых нет в разрешенных играх.
    for game in users_game:
        list_allowed_id.append(game.game_id)
        if game.game_id not in body.game_id:
            list_delete.append(game)

    # Создаем разрешения на игры
    for game_id in body.game_id:
        if game_id not in list_allowed_id:
            ga = AllowedGames()
            ga.id = str(uuid.uuid4())
            ga.user_id = body.user_id
            ga.game_id = game_id
            session.add(ga)

    for del_game in list_delete:
        session.delete(del_game)

    session.commit()

    return 'Success'


async def get_game_allowed(session: Session, user_id: str):
    res = session.query(Games)\
        .join(AllowedGames, AllowedGames.user_id == user_id, isouter=True)\
        .filter(Games.id == AllowedGames.game_id)\
        .all()
    return res


class MakeStatistics:
    def __init__(self, session: Session, user_id: str, year: int = None):
        self.user_id = user_id
        self.session = session
        self.current_year = year if year else datetime.now().year
        self.responce = self.get_responce()
        self.request = self.get_request()

    def __del__(self):
        self.session.close()

    def get_request(self) -> List[GamesPlayed]:
        res = self.session.query(GamesPlayed).filter(GamesPlayed.user_id == self.user_id).filter(
            extract('year', GamesPlayed.created_utc) == self.current_year).all()
        return res

    def get_request_place(self) -> List[GamesPlayed]:
        palitra_id = self.session.query(Games).filter(Games.code_name == 'palitra').first()
        volume_id = self.session.query(Games).filter(Games.code_name == 'volume').first()
        field = func.sum(GamesPlayed.points).label('point')
        place_palitra = self.session.query(GamesPlayed.user_id,
                                           field) \
            .filter(extract('year', GamesPlayed.created_utc) == self.current_year) \
            .filter(GamesPlayed.game_id == palitra_id.id) \
            .group_by(GamesPlayed.user_id) \
            .order_by(field.desc()) \
            .all()
        place_volume = self.session.query(GamesPlayed.user_id,
                                          field) \
            .filter(extract('year', GamesPlayed.created_utc) == self.current_year) \
            .filter(GamesPlayed.game_id == volume_id.id) \
            .group_by(GamesPlayed.user_id) \
            .order_by(field.desc()) \
            .all()
        for index, val in enumerate(place_palitra):
            if val[0] == self.user_id:
                self.responce['game_palitra']['place'][0] = index + 1
        self.responce['game_palitra']['place'][1] = len(place_palitra)

        for index, val in enumerate(place_volume):
            if val[0] == self.user_id:
                self.responce['game_volume']['place'][0] = index + 1
        self.responce['game_volume']['place'][1] = len(place_volume)

    def get_responce(self) -> dict:
        return {
            'game_palitra': {
                'games': [0] * 12,
                'points': [0] * 12,
                'place': [0] * 2
            },
            'game_volume': {
                'games': [0] * 12,
                'points': [0] * 12,
                'place': [0] * 2
            }
        }

    def to_snake_case(self, val: str) -> str:
        return '_'.join(val.split('-'))

    def create(self) -> dict:
        for i in self.request:
            val: GamesPlayed = i
            self.responce.get(f'game_{val.rel_games.code_name}')['games'][val.created_utc.month - 1] += 1
            self.responce.get(f'game_{val.rel_games.code_name}')['points'][val.created_utc.month - 1] += val.points
        self.get_request_place()
        years = self.session.query(extract('year', GamesPlayed.created_utc).label('year')).filter(
            GamesPlayed.user_id == self.user_id).group_by('year').all()
        temp = []
        for i in range(len(years)):
            temp.append(int(years[i][0]))
        year = datetime.now().year
        if year not in temp:
            temp.append(year)
        self.responce['years'] = temp
        return self.responce

