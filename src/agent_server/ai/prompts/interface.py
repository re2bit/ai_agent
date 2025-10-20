import abc
from typing import Any
from abc import ABC, abstractmethod

class IPromptTemplateFactoryInterface(ABC):
    @classmethod
    @abstractmethod
    def create(cls, *args: Any, **kwargs: Any) -> str:
        pass