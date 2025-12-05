from types import UnionType
from typing import Any, Dict, TypeVar, Type, get_type_hints, get_origin, get_args, Union, Optional

from sqlalchemy import inspect
from sqlalchemy.orm.relationships import _RelationshipDeclared
from sqlalchemy.orm.base import RelationshipDirection
from sqlmodel import SQLModel, Session


S = TypeVar("S", bound=Dict[str, Any]) # Normally a TypedDict
K = TypeVar("K", bound=SQLModel)

class StateModelMapper:
    def __init__(self, session: Session | None = None, should_sync: bool = True):
        self.should_sync: bool = should_sync
        self.session: Session | None = session
        self._refresh_after_sync: list[SQLModel] = []

    def map_state_to_model(self, state: S, model: Type[K] | K) -> K:
        if isinstance(model, SQLModel):
            model_instance = model
            model = model_instance.__class__
        if issubclass(model, SQLModel):
            model_instance = None
        else:
            raise Exception("Model is not an SQLModel")

        model_instance = self.process_attributes(model, model_instance, state)

        if self.should_sync:
            self.sync(model_instance)

        return model_instance

    def sync(self, model: SQLModel):
        if self.session is not None:
            self.session.add(model)
            self._refresh_after_sync.append(model)
            self.session.commit()
            self.refresh_after_sync()
        else:
            raise Exception("Session is not available")

    def process_attributes(self, model: type[SQLModel] | type[K], model_instance: Optional[SQLModel], state: S) -> SQLModel:
        mapper = inspect(model, False)
        if mapper is None:
            raise Exception(f"Mapper is None")
        columns = list(mapper.columns)
        rels = list(mapper.relationships)

        if model_instance is None:
            pk_cols = list(mapper.primary_key)
            instance: Optional[K] = None

            if pk_cols and self.session is not None:
                pk_values: list[object] = []

                for col in pk_cols:
                    key = col.key
                    value = state.get(key) if isinstance(state, dict) else getattr(state, key, None)

                    if value is None:
                        pk_values = []
                        break

                    pk_values.append(value)

                if pk_values:
                    identity = pk_values[0] if len(pk_values) == 1 else tuple(pk_values)
                    try:
                        instance = self.session.get(model, identity)
                    except Exception:
                        instance = None

            if instance is None:
                instance = model()

            model_instance = instance

        annotations = get_type_hints(model)

        for key, value in state.items():
            rel = next((item for item in rels if item.key == key), None)

            done = False

            if rel is not None:
                done = self.process_relationship(
                    annotations=annotations,
                    key=key,
                    value=value,
                    rel=rel,
                    model=model,
                    model_instance=model_instance
                )

            if done:
                continue

            col = next((item for item in columns if item.key == key), None)
            if col is not None:
                done = self.process_value(
                    annotations=annotations,
                    key=key,
                    value=value,
                    model_instance=model_instance,
                    model=model
                )

            if done:
                continue

            raise Exception(f"Field {key} is not correct type")

        return model_instance

    def process_value(self, annotations: dict[str, Any], key, value, model: type[SQLModel] | type[K], model_instance: SQLModel | Any) -> bool:
        model_key = model.model_fields.get(key)
        if model_key is None:
            return True

        types_for_key = annotations.get(key)

        if types_for_key is None:
            return True

        origin = get_origin(types_for_key)

        if origin is Union or isinstance(types_for_key, UnionType):
            valid_instance_types = get_args(types_for_key)
        else:
            valid_instance_types = (types_for_key,)

        valid = type(value) in valid_instance_types

        if valid:
            setattr(model_instance, key, value)
            return True

        return False

    def process_relationship(self, annotations: dict[str, Any], key: str, value, rel: _RelationshipDeclared, model: type[SQLModel] | type[K], model_instance: SQLModel | Any) -> bool:
        if rel.direction is RelationshipDirection.MANYTOONE:
            # For now, do not auto-create MANYTOONE from dict to avoid ambiguity
            return True
        elif rel.direction is RelationshipDirection.ONETOMANY or rel.direction is RelationshipDirection.MANYTOMANY:
            if value is None:
                return True

            target_class = rel.entity.class_

            if isinstance(value, list):
                built_items = []
                for item in value:
                    if isinstance(item, dict):
                        # Let process_attributes decide to fetch existing by PK or create new
                        child_instance = self.process_attributes(target_class, None, item)
                        # If a session is available, add to the session and mark for refresh later
                        if self.session is not None:
                            self.session.add(child_instance)
                            self._refresh_after_sync.append(child_instance)
                        built_items.append(child_instance)
                    else:
                        built_items.append(item)
                setattr(model_instance, key, built_items)
                return True
            else:
                return False
        else:
            return True

    def refresh_after_sync(self) -> None:
        """Refresh all instances that were created by the mapper after a commit/flush.

        Call this after `session.commit()` to ensure autoincremented primary keys and
        other database-populated fields are loaded on the instances.
        """
        if self.session is None:
            # Nothing to do without a session
            self._refresh_after_sync.clear()
            return
        try:
            for instance in self._refresh_after_sync:
                try:
                    self.session.refresh(instance)
                except Exception:
                    # Ignore refresh errors for safety; caller may handle as needed
                    pass
        finally:
            self._refresh_after_sync.clear()

    def map_model_to_state(self, state: S, model: Type[K]) -> S:
        pass

