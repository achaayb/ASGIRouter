# CoreAPI

Core is a high-performance lightweight framework for building API's in python with no extra dependencies based on the ASGI specification

The idea of CoreAPI is to be extended and customised based on your needs

Refactored Features:
- **ASGI Compliance:** The framework is designed to be ASGI compliant, ensuring compatibility with asynchronous web servers.
  
- **Decorator Routing:** Simplify your code structure with decorator-based routing, making it more intuitive and modular.

- **URL and Params Parsing:** Efficient handling of URL parsing and parameter extraction for cleaner and more organized route definitions.

- **Request Object Encapsulation:** Request handling is encapsulated within a dedicated object, promoting better code organization and readability.

- **Websocket Support:** Native support for WebSockets, enabling real-time communication and interaction with clients.

- **Thread Pool Execution for Sync Routes:** Enhance performance by utilizing a thread pool for synchronous route execution, ensuring responsiveness even for blocking operations.

```py
# Example app
from coreapi import CoreAPI
from coreapi import Request
from coreapi import JSONResponse
from coreapi import WebSocketConnection

app = CoreAPI()

@app.route(
    "/{hello}",
    methods=["GET", "POST"]
)
def hello_world(request: Request):
    hello = request.slugs["hello"]
    if request.method == "GET":
        return JSONResponse(data={"Hello": hello}, status=200)
    elif request.method == "POST":
        return JSONResponse(data={"Hello": hello}, status=201)


@app.ws("/ws")
async def foo(connection: WebSocketConnection):
    await connection.accept()
    while True:
        message = await connection.receive_message()
        if message == "close":
            await connection.close()
            return
        await connection.send_message(str(message))

```
