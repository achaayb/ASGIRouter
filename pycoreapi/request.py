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
        if isinstance(self.body, dict):
            return self.body
        return json.loads(self.body)

    @property
    def dict(self) -> object:
        return {
            "path": self.path,
            "method": self.method,
            "headers": self.headers,
            "query": self.query,
            "slugs": self.slugs,
            "body": self.json,
        }
    
    @property
    def dict_minified(self) -> object:
        return {
            "headers": self.headers,
            "query": self.query,
            "body": self.json,
        }