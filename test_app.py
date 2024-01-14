from coreapi.core import CoreAPI
from coreapi.request import Request
from coreapi.response import JSONResponse
from coreapi.connection import WebSocketConnection

app = CoreAPI()

@app.route(
    "/{hello}",
    methods=["POST"]
)
def hello_world(request: Request):
    hello = request.slugs["hello"]
    response = JSONResponse(
        data={"name": request.headers["foo"]}, status=200
    )
    response.set_header("Hello", "World")
    return response


@app.ws("/")
async def foo(connection: WebSocketConnection):
    await connection.accept()
    while True:
        message = await connection.receive_message()
        if message == "close":
            await connection.close()
            return
        await connection.send_message(str(message))
