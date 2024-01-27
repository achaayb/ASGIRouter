# request.py
import json
from typing import Any


class Request:
    proto: Any
    path: str
    method: str
    headers: dict[str, str]
    query: dict[str, str]
    slugs: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode()

    @property
    def json(self) -> object:
        if not self.body:
            return {}
        return json.loads(self.body)

    @property
    def dict(self) -> object:
        return {
            "path": self.path,
            "method": self.method,
            "headers": self.headers,
            "query": self.query,
            "slugs": self.slugs,
            "body": self.text,
        }
