# ASGIRouter

ASGIRouter is a lightweight and flexible ASGI routing library for Python web applications. It allows you to define HTTP and WebSocket routes with middleware support.

## Installation

No external dependencies are required. Simply copy the `router.py` file into your project.

## Usage

### Basic Example

```python
from router import ASGIRouter

app = ASGIRouter()

# Middleware example
async def shared_middleware(scope, receive, send):
    print(scope["path_params"].get("foo"))

# HTTP route example
@app.route("/{foo}", methods=["GET", "POST"], middleware=shared_middleware)
async def example(scope, receive, send):
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"text/plain"]],
    })
    await send({"type": "http.response.body", "body": b"Hello, world!"})

# WebSocket route example
@app.ws("/ws")
async def websocket_handler(scope, receive, send):
    while True:
        event = await receive()
        if event["type"] == "websocket.disconnect":
            break
        elif event["type"] == "websocket.connect":
            await send({"type": "websocket.accept"})
        elif event["type"] == "websocket.receive":
            await send({"type": "websocket.send", "text": event["type"]})
```

### Run your application using uvicorn

```bash
uvicorn app:app
```