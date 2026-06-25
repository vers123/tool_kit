from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass(kw_only=True, eq=False)
class ScrapedData(ABC):
    index: int = 0

    @abstractmethod
    def to_line(self) -> str:
        pass

    @abstractmethod
    def get_unique_key(self) -> str:
        pass

    def __hash__(self):
        return hash(self.get_unique_key())

    def __eq__(self, other):
        if isinstance(other, ScrapedData):
            return self.get_unique_key() == other.get_unique_key()
        return False


@dataclass(kw_only=True, eq=False)
class ImageData(ScrapedData):
    name: str
    url: str

    def to_line(self) -> str:
        return f"{self.index:04d}-{self.name}-[{self.url}]"

    def get_unique_key(self) -> str:
        return self.url


@dataclass(kw_only=True, eq=False)
class NewsData(ScrapedData):
    title: str
    url: str
    date: str

    def to_line(self) -> str:
        return f"{self.index:04d}-{self.title}-[{self.date}]-({self.url})"

    def get_unique_key(self) -> str:
        return self.url


@dataclass(kw_only=True, eq=False)
class PostData(ScrapedData):
    title: str
    url: str
    date: str

    def to_line(self) -> str:
        return f"{self.index:04d}-{self.title}-[{self.date}]({self.url})"

    def get_unique_key(self) -> str:
        return self.url


@dataclass(kw_only=True, eq=False)
class CharacterData(ScrapedData):
    id: str
    name: str

    def to_line(self) -> str:
        return f"{self.index:04d}-{self.id}-{self.name}"

    def get_unique_key(self) -> str:
        return self.id


class DataSerializer(ABC):
    @abstractmethod
    def serialize(self, data: List[ScrapedData]) -> str:
        pass

    @abstractmethod
    def deserialize(self, content: str) -> List[ScrapedData]:
        pass


class LineSerializer(DataSerializer):
    def __init__(self, item_class):
        self.item_class = item_class

    def serialize(self, data: List[ScrapedData]) -> str:
        return "\n".join(item.to_line() for item in data)

    def deserialize(self, content: str) -> List[ScrapedData]:
        raise NotImplementedError
