from abc import ABC, abstractmethod
from typing import Any


class IRuntimeGraphPort(ABC):
    @abstractmethod
    async def ainvoke(self, graph_input: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        pass
