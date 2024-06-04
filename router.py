import re
from asyncio import get_event_loop


class ASGIRouter:
    def __init__(self: "ASGIRouter"):
        self._http_routes = []
        self._ws_routes = []
        self._loop = get_event_loop()

    def route(self, path, methods=None, middleware=None):
        if methods is None:
            methods = ["GET"]

        if path.endswith("/"):
            path = path[:-1]

        def decorator(handler):
            self._add_http_route(path, methods, handler, middleware)
            return handler

        return decorator

    def ws(self, path, middleware=None):
        if path.endswith("/"):
            path = path[:-1]

        def decorator(handler):
            self._add_ws_route(path, handler, middleware)
            return handler

        return decorator

    def _add_http_route(self, path, methods, handler, request_middleware):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._http_routes.append(
            (re.compile(path_re), methods, handler, request_middleware)
        )
        return handler

    def _add_ws_route(self, path, handler, connection_middleware):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._ws_routes.append((re.compile(path_re), handler, connection_middleware))
        return handler

    def _match_http(self, scope):
        path_info = scope["path"]
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        request_method = scope["method"]
        for path, methods, handler, request_middleware in self._http_routes:
            # Skip if invalid method
            if request_method not in methods:
                continue
            m = path.match(path_info)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {
                    "path_params": path_params,
                    "handler": handler,
                    "request_middleware": request_middleware,
                }

    def _match_ws(self, scope):
        path_info = scope["path"]
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        for path, handler, connection_middleware in self._ws_routes:
            m = path.match(path_info)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {
                    "path_params": path_params,
                    "handler": handler,
                    "connection_middleware": connection_middleware,
                }

    async def _http_handler(self, scope, receive, send):
        # Match request with defined routes
        match = self._match_http(scope)

        # Return 404 if no match is found
        if match is None:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        [b"content-type", b"text/plain"],
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b"Not found"})
            return
        # Inject path parameters in scope
        scope["path_params"] = match["path_params"]

        # Execute request middleware
        request_middleware = match.get("request_middleware", None)
        if request_middleware:
            await match["request_middleware"](scope, receive, send)

        # Execute request handler
        await match["handler"](scope, receive, send)

    async def _ws_handler(self, scope, receive, send):
        # Match websocket connection to defined routes
        match = self._match_ws(scope)
        # Return 404 if no match is found
        if match is None:
            await send.close(404)
            return

        # Inject path parameters in scope
        scope["path_params"] = match["path_params"]

        # Execute connection middleware
        connection_middleware = match.get("connection_middleware", None)
        if connection_middleware:
            await match["connection_middleware"](scope, receive, send)

        # Execute connection handler
        await match["handler"](scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            await self._http_handler(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._ws_handler(scope, receive, send)
