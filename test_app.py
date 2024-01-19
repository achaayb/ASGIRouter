from time import sleep

from coreapi import CoreAPI, JSONResponse, Request, WebSocketConnection

app = CoreAPI()


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
