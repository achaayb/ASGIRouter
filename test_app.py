from coreapi import WebSocketConnection

from coreapi import CoreAPI
from coreapi import Request
from coreapi import JSONResponse
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
