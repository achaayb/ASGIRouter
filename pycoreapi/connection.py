# connection.py
from enum import Enum
from typing import Any, Union

from pycoreapi.exceptions import WebSocketClosedByClient


class WebsocketMessageType(int, Enum):
    close = 0
    bytes = 1
    string = 2


class WebSocketMessage:
    kind: WebsocketMessageType
    data: Union[bytes, str]

    @property
    def type(self) -> bytes | str:
        if self.kind == 1:
            return bytes
        elif self.kind == 2:
            return str


class WebSocketConnection:
    proto: Any
    path: str
    headers: dict[str, str]
    query: dict[str, str]
    slugs: dict[str, str]
    rsgi_websocket_protocol: Any | None = None

    async def accept(self):
        self.rsgi_websocket_protocol = await self.proto.accept()

    async def receive(self) -> WebSocketMessage:
        _websocket_message = await self.rsgi_websocket_protocol.receive()
        websocket_message = WebSocketMessage()
        websocket_message.kind = _websocket_message.kind
        if websocket_message.kind == 0:  # Closed by client
            raise WebSocketClosedByClient
        websocket_message.data = _websocket_message.data

        return websocket_message

    async def send(self, message):
        if isinstance(message, str):
            await self.rsgi_websocket_protocol.send_str(message)
        elif isinstance(message, bytes):
            await self.rsgi_websocket_protocol.send_bytes(message)
        else:
            raise TypeError("Invalid message type str|bytes only")

    async def close(self, code=1000):
        self.proto.close(status=code)
