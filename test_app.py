from coreapi import WebSocketConnection

from coreapi import CoreAPI
from coreapi import Request
from coreapi import JSONResponse
from time import sleep
from asyncio import sleep as async_sleep

app = CoreAPI(pool_size=4)

@app.route("/foo")
def sync_controller(request):
    sleep(1)
    return JSONResponse({"type": "sync"})

@app.route("/async")
async def async_controller(request):
    return JSONResponse({"type": "async"})


@app.ws("/ws")
async def foo(connection: WebSocketConnection):
    await connection.accept()
    while True:
        message = await connection.receive_message()
        if message == "close":
            await connection.close()
            return
        await connection.send_message(str(message))
