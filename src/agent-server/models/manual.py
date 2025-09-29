from __future__ import annotations
from typing import Optional, List
import sqlalchemy as sa
from sqlmodel import Field, SQLModel, Relationship


class Manual(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: Optional[int] = Field(default=None, foreign_key="game.id", index=True)
    game: Optional[Game] = Relationship(back_populates="manuals")


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    year: Optional[int] = Field(default=None, index=True)
    platform: Optional[int] = Field(default=None, foreign_key="platform.id", index=True)
    genre: Optional[int] = Field(default=None, foreign_key="genre.id", index=True)
    publisher: Optional[int] = Field(default=None, foreign_key="publisher.id", index=True)
    size: Optional[int] = Field(default=None, index=True)
    description: Optional[str] = Field(default=None, index=True)
    manuals: List[Manual] = Relationship(back_populates="game")
    platform_obj: Optional[Platform] = Relationship(sa_relationship_kwargs={"primaryjoin": "Game.platform==Platform.id"})
    genre_obj: Optional[Genre] = Relationship(sa_relationship_kwargs={"primaryjoin": "Game.genre==Genre.id"})
    publisher_obj: Optional[Publisher] = Relationship(sa_relationship_kwargs={"primaryjoin": "Game.publisher==Publisher.id"})

class Genre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)

class Publisher(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)


class Platform(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    processor: Optional[str] = Field(default=None, index=True)
