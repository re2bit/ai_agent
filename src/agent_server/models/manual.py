from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint


class Manual(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: Optional[int] = Field(default=None, foreign_key="game.id", index=True)

    sources: list["ManualSource"] = Relationship(back_populates="manual")
    downloads: list["IADownload"] = Relationship(back_populates="manual")

    game: Optional["Game"] = Relationship(back_populates="manuals")


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    year: Optional[int] = Field(default=None, index=True)
    platform: Optional[int] = Field(default=None, foreign_key="platform.id", index=True)
    genre: Optional[int] = Field(default=None, foreign_key="genre.id", index=True)
    publisher: Optional[int] = Field(default=None, foreign_key="publisher.id", index=True)
    size: Optional[int] = Field(default=None, index=True)
    description: Optional[str] = Field(default=None, index=True)

    manuals: list["Manual"] = Relationship(back_populates="game")
    platform_obj: Optional["Platform"] = Relationship(sa_relationship_kwargs={"primaryjoin": "Game.platform==Platform.id"})
    genre_obj: Optional["Genre"] = Relationship(sa_relationship_kwargs={"primaryjoin": "Game.genre==Genre.id"})
    publisher_obj: Optional["Publisher"] = Relationship(sa_relationship_kwargs={"primaryjoin": "Game.publisher==Publisher.id"})


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


class IASearch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query: str

    cached_results: Optional[bool] = None
    cached_filtered: Optional[bool] = None
    cached_metadata: Optional[bool] = None

    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    results: list["IASearchResult"] = Relationship(back_populates="search")
    filtered: list["IAFilteredResult"] = Relationship(back_populates="search")
    consider: list["IAEntryToConsider"] = Relationship(back_populates="search")
    pdfs: list["IAPdfToDownload"] = Relationship(back_populates="search")
    downloads: list["IADownload"] = Relationship(back_populates="search")
    manual_sources: list["ManualSource"] = Relationship(back_populates="search")

class IASearchResult(SQLModel, table=True):
    search_id: int = Field(foreign_key="iasearch.id", primary_key=True)
    rank: int = Field(primary_key=True)
    identifier: str

    search: Optional["IASearch"] = Relationship(back_populates="results")

class IAFilteredResult(SQLModel, table=True):
    search_id: int = Field(foreign_key="iasearch.id", primary_key=True)
    rank: int = Field(primary_key=True)
    identifier: str

    search: Optional["IASearch"] = Relationship(back_populates="filtered")


class IAItem(SQLModel, table=True):
    identifier: str = Field(primary_key=True)

    mediatype: Optional[str] = None
    title: Optional[str] = None
    creator: Optional[str] = None
    date: Optional[str] = None
    language: Optional[str] = None
    uploader: Optional[str] = None
    publicdate: Optional[str] = None
    addeddate: Optional[str] = None
    description: Optional[str] = None
    scanner: Optional[str] = None
    ocr: Optional[str] = None
    ocr_parameters: Optional[str] = None
    ocr_module_version: Optional[str] = None
    ocr_detected_lang: Optional[str] = None
    ocr_detected_lang_conf: Optional[str] = None

    #metadata_json: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    collections: list["IAItemCollection"] = Relationship(back_populates="item")
    subjects: list["IAItemSubject"] = Relationship(back_populates="item")
    files: list["IAItemFile"] = Relationship(back_populates="item")


class IAItemCollection(SQLModel, table=True):
    identifier: str = Field(foreign_key="iaitem.identifier", primary_key=True)
    collection: str = Field(primary_key=True)
    item: Optional["IAItem"] = Relationship(back_populates="collections")


class IAItemSubject(SQLModel, table=True):
    identifier: str = Field(foreign_key="iaitem.identifier", primary_key=True)
    subject: str = Field(primary_key=True)
    item: Optional["IAItem"] = Relationship(back_populates="subjects")


class IAItemFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identifier: str = Field(foreign_key="iaitem.identifier", index=True)
    name: str
    source: Optional[str] = None
    format: Optional[str] = None
    original: Optional[str] = None
    mtime: Optional[int] = None  # Unix epoch
    size_bytes: Optional[int] = Field(default=None, alias="size")
    md5: Optional[str] = None
    crc32: Optional[str] = None
    sha1: Optional[str] = None
    #extra_json: Optional[Dict[str, Any]] = None

    item: Optional["IAItem"] = Relationship(back_populates="files")
    manual_links: list["ManualSource"] = Relationship(back_populates="item_file")

    __table_args__ = (
        UniqueConstraint("identifier", "name", name="uq_iaitemfile_identifier_name"),
    )


class IAEntryToConsider(SQLModel, table=True):
    search_id: int = Field(foreign_key="iasearch.id", primary_key=True)
    rank: int = Field(primary_key=True)
    identifier: str = Field(foreign_key="iaitem.identifier")

    search: Optional["IASearch"] = Relationship(back_populates="consider")


class IAPdfToDownload(SQLModel, table=True):
    search_id: int = Field(foreign_key="iasearch.id", primary_key=True)
    identifier: str = Field(foreign_key="iaitem.identifier", primary_key=True)
    file_name: str = Field(primary_key=True)

    search: Optional["IASearch"] = Relationship(back_populates="pdfs")


class IADownload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    search_id: Optional[int] = Field(default=None, foreign_key="iasearch.id", index=True)
    identifier: Optional[str] = Field(default=None, foreign_key="iaitem.identifier", index=True)
    file_name: str

    manual_id: Optional[int] = Field(default=None, foreign_key="manual.id", index=True)

    target_path: str
    status: str  # 'queued' | 'ok' | 'failed'
    bytes_written: Optional[int] = None
    checksum_ok: Optional[bool] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    search: Optional["IASearch"] = Relationship(back_populates="downloads")
    manual: Optional["Manual"] = Relationship(back_populates="downloads")


class ManualSource(SQLModel, table=True):
    manual_id: int = Field(foreign_key="manual.id", primary_key=True)
    identifier: str = Field(primary_key=True)
    file_name: str = Field(primary_key=True)
    search_id: Optional[int] = Field(default=None, foreign_key="iasearch.id", index=True)

    # Backrefs
    manual: Optional["Manual"] = Relationship(back_populates="sources")
    search: Optional["IASearch"] = Relationship(back_populates="manual_sources")
    item_file: Optional["IAItemFile"] = Relationship(back_populates="manual_links",
                                         sa_relationship_kwargs={
                                             "primaryjoin":
                                                 "and_(ManualSource.identifier==IAItemFile.identifier, "
                                                 "ManualSource.file_name==IAItemFile.name)"
                                         })

    __table_args__ = (
        # Composite FK auf IAItemFile(identifier, name)
        ForeignKeyConstraint(
            ["identifier", "file_name"],
            ["iaitemfile.identifier", "iaitemfile.name"],
            name="fk_manualsource_file"
        ),
    )