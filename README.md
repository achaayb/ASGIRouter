# CoreAPI

Core is a high-performance lightweight framework for building API's in python with no extra dependencies based on the ASGI specification

The idea of CoreAPI is to be extended and customised based on your needs

**Features**:
- **ASGI Compliance:** The framework is designed to be ASGI compliant, ensuring compatibility with asynchronous web servers.
  
- **Decorator Routing:** Simplify your code structure with decorator-based routing, making it more intuitive and modular.

- **URL and Params Parsing:** Efficient handling of URL parsing and parameter extraction for cleaner and more organized route definitions.

- **Request Object Encapsulation:** Request handling is encapsulated within a dedicated object, promoting better code organization and readability.

- **Websocket Support:** Native support for WebSockets, enabling real-time communication and interaction with clients.

- **Thread Pool Execution for Sync Routes:** Enhance performance by utilizing a thread pool for synchronous route execution, ensuring responsiveness even for blocking operations.

```py
from coreapi import CoreAPI
from coreapi import Request
from coreapi import JSONResponse
from coreapi import WebSocketConnection
from time import sleep

app = CoreAPI(pool_size=4)

@app.route("/foo")
def sync_controller(request: Request) -> JSONResponse:
    sleep(1)
    return JSONResponse({"type": "sync"})

@app.route("/async")
async def async_controller(request: Request) -> JSONResponse:
    return JSONResponse({"type": "async"})


@app.ws("/ws")
async def foo(connection: WebSocketConnection) -> None:
    await connection.accept()
    while True:
        message = await connection.receive_message()
        if message == "close":
            await connection.close()
            return
        await connection.send_message(str(message))

```
