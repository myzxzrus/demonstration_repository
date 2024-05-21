from typing import Optional, List
from pydantic import BaseModel, validator, conlist
import datetime
from enum import Enum


class GamesPlayedScheme(BaseModel):
    id: str = None
    created_utc: datetime.datetime = None
    updated_utc: datetime.datetime = None
    user_id: str = None
    game: str = None
    points: int = None

    class Config:
        orm_mode = True


class GamesScheme(BaseModel):
    id: str = None
    created_utc: datetime.datetime = None
    updated_utc: datetime.datetime = None
    name: str = None
    code_name: str = None
    descriptions: str = None

    class Config:
        orm_mode = True


class AllowedGamesScheme(GamesScheme):
    game_id: str = None


class GamesPlayedResponseScheme(BaseModel):
    id: str = None
    created_utc: datetime.datetime = None
    updated_utc: datetime.datetime = None
    user_id: str = None
    game: str = None
    points: int = None


class PlayedCreateScheme(BaseModel):
    user_id: str
    game_id: str
    points: int


class AllowedGameCreateScheme(BaseModel):
    user_id: str
    game_id: List[str]


class StatisticsGameScheme(BaseModel):
    games: conlist(int, min_items=12, max_items=12)
    points: conlist(int, min_items=12, max_items=12)
    place: conlist(int, min_items=2, max_items=2)


class StatisticsResponseScheme(BaseModel):
    game_palitra: Optional[StatisticsGameScheme]
    game_volume: Optional[StatisticsGameScheme]
    years: List[int]


