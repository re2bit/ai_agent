from sqlmodel import Field, SQLModel

class Manual(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    game_id: int | None = Field(default=None, index=True)

class Game(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    year: int | None = Field(default=None, index=True)
    platform: int | None = Field(default=None, index=True)
    genre: int | None = Field(default=None, index=True)
    publisher: int | None = Field(default=None, index=True)
    size: int | None = Field(default=None, index=True)
    description: str | None = Field(default=None, index=True)

class Genre(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

class Publisher(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

class platform(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    processor: str | None = Field(default=None, index=True)