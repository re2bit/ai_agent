
import unittest
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Relationship, Field, Session, create_engine, select

from agent_server.adapters.database import StateModelMapper


# Simple Model
class DummyModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="")

# One-to-many
class Many(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    one_id: Optional[int] = Field(default=None, foreign_key="one.id")
    data: str = Field(default="")
    one: Optional["One"] = Relationship(back_populates="many")

class One(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data: Optional[str] = Field(default="")
    many: Mapped[List['Many']] = Relationship(back_populates="one")

# 2-level nested one-to-many: Top -> Mid (children), Mid -> Sub (grandchildren)
class Sub(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data: str = Field(default="")
    mid_id: Optional[int] = Field(default=None, foreign_key="mid.id")
    mid: Optional["Mid"] = Relationship(back_populates="grandchildren")

class Mid(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data: str = Field(default="")
    top_id: Optional[int] = Field(default=None, foreign_key="top.id")
    top: Optional["Top"] = Relationship(back_populates="children")
    grandchildren: Mapped[List[Sub]] = Relationship(back_populates="mid")

class Top(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data: str = Field(default="")
    children: Mapped[List[Mid]] = Relationship(back_populates="top")

# Many-to-many via association table
class AuthorBookLink(SQLModel, table=True):
    author_id: Optional[int] = Field(default=None, foreign_key="author.id", primary_key=True)
    book_id: Optional[int] = Field(default=None, foreign_key="book.id", primary_key=True)

class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="")
    books: Mapped[List["Book"]] = Relationship(back_populates="authors", link_model=AuthorBookLink)

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="")
    authors: Mapped[List[Author]] = Relationship(back_populates="books", link_model=AuthorBookLink)

# Composite Primary Key model for testing
class CompositeEntity(SQLModel, table=True):
    part_a: int = Field(primary_key=True)
    part_b: int = Field(primary_key=True)
    payload: str = Field(default="")


class TestStateModelMapper(unittest.TestCase):
    engine = None
    db_path: Path | None = None

    @classmethod
    def setUpClass(cls):
        cls.db_path = Path(__file__).with_suffix(".sqlite")

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.engine is not None:
                cls.engine.dispose()
        finally:
            if cls.db_path and cls.db_path.exists():
                try:
                    os.remove(cls.db_path)
                except Exception:
                    pass

    def create_session(self) -> Session:
        return Session(self.engine)

    def setUp(self):
        try:
            if self.engine is not None:
                self.engine.dispose()
        except Exception:
            pass

        try:
            if self.db_path and self.db_path.exists():
                os.remove(self.db_path)
        except Exception:
            pass

        self.__class__.engine = create_engine(f"sqlite:///{self.db_path}")
        SQLModel.metadata.create_all(self.engine)

    def test_instantiate(self):
        mapper = self._create_state_model_mapper()
        self.assertIsInstance(mapper, StateModelMapper)

    def test_methods_exist(self):
        self.assertTrue(hasattr(StateModelMapper, 'map_state_to_model'))
        self.assertTrue(callable(getattr(StateModelMapper, 'map_state_to_model')))

        self.assertTrue(hasattr(StateModelMapper, 'map_model_to_state'))
        self.assertTrue(callable(getattr(StateModelMapper, 'map_model_to_state')))


    def test_simple_map_state_to_model(self):
        model = DummyModel()
        mapper = self._create_state_model_mapper()
        state_simple: Dict[str, Any] = {"id": 1, "name": "example"}
        model = mapper.map_state_to_model(state_simple, model)
        self.assertIsInstance(model, DummyModel)
        self.assertEqual(model.id, 1)


    def test_wrong_type_map_state_to_model(self):
        with self.assertRaises(Exception):
            model = DummyModel()
            mapper = self._create_state_model_mapper()
            state_wrong_type: Dict[str, Any] = {"id": "1"}
            mapper.map_state_to_model(state_wrong_type, model)


    def test_none_value_map_state_to_model(self):
        with self.assertRaises(Exception) as e:
            model = DummyModel()
            mapper = self._create_state_model_mapper()
            state_none: Dict[str, Any] = {"id": "1"}
            mapper.map_state_to_model(state_none, model)
        self.assertEqual(str(e.exception), "Field id is not correct type")


    def test_exception_on_invalid_model(self):
        with self.assertRaises(Exception) as e:
            mapper = self._create_state_model_mapper()
            mapper.map_state_to_model({}, str)
        self.assertEqual(str(e.exception), "Model is not an SQLModel")


    def test_one_to_many_map_state_to_model(self):
        one = One()
        mapper = self._create_state_model_mapper()
        state: Dict[str, Any] = {
            "id": 1,
            "data": "one",
            "many": [
                {"id": 1, "data": "many1"},
                {"id": 2, "data": "many2"}
            ]
        }
        model = mapper.map_state_to_model(state, one)
        self.assertIsInstance(model, One)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.data, "one")
        self.assertEqual(len(model.many), 2)
        self.assertEqual(model.many[0].data, "many1")

    def test_one_to_many_without_children_key(self):
        state: Dict[str, Any] = {"id": 2, "data": "without-children"}
        one = One()
        mapper = self._create_state_model_mapper()
        model = mapper.map_state_to_model(state, one)
        self.assertIsInstance(model, One)
        self.assertEqual(model.id, 2)
        self.assertEqual(model.data, "without-children")
        self.assertEqual(len(model.many), 0)

    def test_two_level_nested_one_to_many(self):
        state: Dict[str, Any] = {
            "id": 1,
            "data": "top",
            "children": [
                {
                    "id": 10,
                    "data": "mid1",
                    "grandchildren": [
                        {"id": 100, "data": "sub1"}
                    ]
                },
                {
                    "id": 11,
                    "data": "mid2",
                    "grandchildren": [
                        {"id": 101, "data": "sub2"},
                        {"id": 102, "data": "sub3"}
                    ]
                }
            ]
        }
        mapper = self._create_state_model_mapper()
        top = Top()
        model = mapper.map_state_to_model(state, top)
        self.assertIsInstance(model, Top)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.data, "top")
        self.assertEqual(len(model.children), 2)
        self.assertEqual(model.children[0].data, "mid1")
        self.assertEqual(len(model.children[0].grandchildren), 1)
        self.assertEqual(model.children[0].grandchildren[0].data, "sub1")
        self.assertEqual(len(model.children[1].grandchildren), 2)
        self.assertEqual(model.children[1].grandchildren[1].data, "sub3")

    def test_many_to_many_map_state_to_model(self):
        state: Dict[str, Any] = {
            "id": 1,
            "name": "author1",
            "books": [
                {"id": 10, "title": "book1"},
                {"id": 11, "title": "book2"}
            ]
        }
        mapper = self._create_state_model_mapper()
        author = Author()
        model = mapper.map_state_to_model(state, author)
        self.assertIsInstance(model, Author)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "author1")
        self.assertEqual(len(model.books), 2)
        self.assertEqual(model.books[0].title, "book1")

    def test_persist_simple_one_to_many_saves_to_db(self):
        with self.create_session() as session:
            mapper = StateModelMapper(session)
            one = One()
            state: Dict[str, Any] = {
                "data": "one",
                "many": [
                    {"data": "child1"},
                    {"data": "child2"},
                ],
            }
            one = mapper.map_state_to_model(state, one)
            persisted_one_id = one.id
            self.assertIsNotNone(persisted_one_id)

        with self.create_session() as check_session:
            ones = list(check_session.exec(select(One)))
            manys = list(check_session.exec(select(Many)))

            self.assertEqual(len(ones), 1)
            self.assertEqual(len(manys), 2)

            db_one = ones[0]
            self.assertEqual(db_one.data, "one")
            for m in manys:
                self.assertEqual(m.one_id, db_one.id)
            self.assertCountEqual([m.data for m in manys], ["child1", "child2"])

    def test_map_state_to_existing_one_updates_and_persists_children(self):
        with self.create_session() as session:
            existing = One(id=42, data="before")
            session.add(existing)
            session.commit()
            session.refresh(existing)

            mapper = StateModelMapper(session)
            state: Dict[str, Any] = {
                "id": 42,
                "data": "after",
                "many": [
                    {"data": "m1"},
                    {"data": "m2"},
                ],
            }
            mapper.map_state_to_model(state, existing)

        with self.create_session() as check_session:
            ones = list(check_session.exec(select(One)))
            manys = list(check_session.exec(select(Many)))

            self.assertEqual(len(ones), 1)
            db_one = ones[0]
            self.assertEqual(db_one.id, 42)
            self.assertEqual(db_one.data, "after")

            self.assertEqual(len(manys), 2)
            for m in manys:
                self.assertEqual(m.one_id, db_one.id)
            self.assertCountEqual([m.data for m in manys], ["m1", "m2"]) 

    def test_map_state_to_existing_one_updates_and_persists_children_with_class(self):
        with self.create_session() as session:
            one = One(id=42, data="before")
            session.add(one)
            session.commit()
            session.refresh(one)

            mapper = StateModelMapper(session)
            state: Dict[str, Any] = {
                "id": 42,
                "data": "after",
                "many": [
                    {"data": "m1"},
                    {"data": "m2"},
                ],
            }
            mapper.map_state_to_model(state, One)

        with self.create_session() as check_session:
            ones = list(check_session.exec(select(One)))
            manys = list(check_session.exec(select(Many)))

            self.assertEqual(len(ones), 1)
            db_one = ones[0]
            self.assertEqual(db_one.id, 42)
            self.assertEqual(db_one.data, "after")

            self.assertEqual(len(manys), 2)
            for m in manys:
                self.assertEqual(m.one_id, db_one.id)
            self.assertCountEqual([m.data for m in manys], ["m1", "m2"])


    def test_composite_primary_key_update(self):
        # Arrange: create an existing entity with a composite primary key
        with self.create_session() as session:
            existing = CompositeEntity(part_a=1, part_b=2, payload="original")
            session.add(existing)
            session.commit()
            session.refresh(existing)

            # Act: use the mapper to update the existing entity using its composite PK
            mapper = StateModelMapper(session)
            state: Dict[str, Any] = {
                "part_a": 1,
                "part_b": 2,
                "payload": "updated",
            }
            # Provide the class so the mapper can fetch by PK and update
            mapper.map_state_to_model(state, CompositeEntity)

        # Assert: verify exactly one row exists with updated payload
        with self.create_session() as check_session:
            rows = list(check_session.exec(select(CompositeEntity)))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.part_a, 1)
            self.assertEqual(row.part_b, 2)
            self.assertEqual(row.payload, "updated")

    def _create_state_model_mapper(self) -> StateModelMapper:
        return StateModelMapper(self.create_session())


if __name__ == "__main__":
    unittest.main()
