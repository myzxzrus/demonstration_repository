from fastapi import APIRouter, Depends, status
from .schemas import *
from sqlalchemy.orm import Session
from ...session import get_db
from .service import create_game_played, MakeStatistics, get_game_classifier, create_game_allowed, get_game_allowed
from ..auth.service import get_current_user
from ..auth.schemas import TokenData
from ...config import Config
from ...models.schemas import BaseResponseSchema

base_url = Config.base_url

router = APIRouter(tags=['Games'], prefix=f'{base_url}/game')


@router.get("/games_classifier", response_model=List[GamesScheme])
async def get_games_classifier(session: Session = Depends(get_db),
                               current_user: TokenData = Depends(get_current_user)) -> List[GamesScheme]:
    """Получения классификатора игр"""
    if current_user:
        res = await get_game_classifier(session)
        return res


@router.get("/games_allowed/{user_id}", response_model=List[GamesScheme])
async def get_games_allowed(user_id: str, session: Session = Depends(get_db),
                               current_user: TokenData = Depends(get_current_user)) -> List[AllowedGamesScheme]:
    """Получения игр доступных пользователям"""
    if current_user:
        res = await get_game_allowed(session, user_id)
        return res


@router.post("/games_allowed", status_code=status.HTTP_201_CREATED, response_model=BaseResponseSchema)
async def set_game_allowed(body: AllowedGameCreateScheme, session: Session = Depends(get_db),
                      current_user: TokenData = Depends(get_current_user)) -> dict:
    """Создание обновление доступных игр для пользователя"""
    if current_user.role == 'admin' or current_user.role == 'superadmin':
        await create_game_allowed(session, body)
        return {'msg': 'Разрешение добавлено'}


@router.post("/played", status_code=status.HTTP_201_CREATED, response_model=GamesPlayedScheme)
async def set_played_game(body: PlayedCreateScheme, session: Session = Depends(get_db),
                      current_user: TokenData = Depends(get_current_user)) -> GamesPlayedScheme:
    """Создание записи об сыгранной игре"""
    if current_user:
        new_user = await create_game_played(session, body)
        return new_user


@router.get("/users_statistics", response_model=StatisticsResponseScheme)
async def get_users_statistics(user_id: str, year: str = None, session: Session = Depends(get_db),
                               current_user: TokenData = Depends(get_current_user)) -> StatisticsResponseScheme:
    """Получение статистики за пользователя по играм"""
    if current_user:
        statistics = MakeStatistics(session, user_id, year)
        # statistics.make_data()
        res = statistics.create()
        return res


