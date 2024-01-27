# response.py
import json
from typing import Any, Dict, Union


class JSONResponse:
    def __init__(
        self,
        data: Union[Dict[str, Any], list[Dict[str, Any]]] = None,
        status: str = 200,
        headers: list[tuple[str, str]] = [("Content-Type", "application/json")],
    ):
        self.data = data
        self.status = status
        self.headers = headers

    def set_header(self, key: str, value: str) -> None:
        # Check if the header already exists
        for i, (existing_key, _) in enumerate(self.headers):
            if existing_key == key:
                # Update the existing header
                self.headers[i] = (key, value)
                break
        else:
            # Add a new header if it doesn't exist
            self.headers.append((key, value))

    @property
    def body(self) -> bytes:
        if self.data is None:
            return "{}"
        elif isinstance(self.data, (dict, list)):
            return json.dumps(self.data)
        else:
            raise TypeError("Invalide response data type")

    @property
    def body(self) -> bytes:
        if self.data is None:
            return "{}"
        elif isinstance(self.data, (dict, list)):
            return json.dumps(self.data)
        else:
            raise TypeError("Invalide response data type")

    @property
    def status_to_str(self) -> str:
        return str(self.status)
