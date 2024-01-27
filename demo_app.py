from time import sleep

from pycoreapi import CoreAPI
from pycoreapi.response import JSONResponse
from pycoreapi.request import Request
from pycoreapi.exceptions import WebSocketClosedByClient
from pycoreapi.connection import WebSocketConnection, WebSocketMessage

app = CoreAPI()


# Sync endpoint demo
@app.route("/sync")
def sync_controller(request: Request) -> JSONResponse:
    sleep(1)
    return JSONResponse({"type": "sync"})


# Async endpoint demo
@app.route("/async")
async def async_controller(request: Request) -> JSONResponse:
    return JSONResponse({"type": "async"})


# Methods demo
@app.route("/methods", methods=["GET", "POST"])
async def post(request: Request) -> JSONResponse:
    if request.method == "POST":
        return JSONResponse({"method": request.method})
    elif request.method == "GET":
        return JSONResponse({"method": request.method})


# Url slugs demo
@app.route("/demo/{demo_id}")
async def post(request: Request) -> JSONResponse:
    return JSONResponse({"user_id": request.slugs["demo_id"]})


# Headers demo
@app.route("/headers")
async def post(request: Request) -> JSONResponse:
    api_key = request.headers.get("api-key", "Not Found")
    response = JSONResponse()
    response.set_header("api-key", api_key)
    return response


# Websocket demo
@app.ws("/ws/{token}")
async def web_socket(connection: WebSocketConnection) -> None:
    # Validate token
    token = connection.slugs["token"]
    if token != "SECRET_TOKEN":
        await connection.close(401)
        return

    # Accept websocket connection
    await connection.accept()
    while True:
        try:
            # Await next message
            message: WebSocketMessage = await connection.receive()
        except WebSocketClosedByClient:
            # Handle client disconnect
            await connection.close()
            return
        await connection.send(message.data)
