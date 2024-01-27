import re
from asyncio import get_event_loop, iscoroutinefunction
from urllib.parse import parse_qs

from pycoreapi.connection import WebSocketConnection
from pycoreapi.request import Request
from pycoreapi.response import JSONResponse


class CoreAPI:
    def __init__(self: "CoreAPI"):
        self._http_routes = []
        self._ws_routes = []
        self._loop = get_event_loop()

    # Exposed decorators
    def route(self, path, methods=None):
        if methods is None:
            methods = ["GET"]

        if path.endswith("/"):
            path = path[:-1]

        def decorator(handler):
            self._add_http_route(path, methods, handler)
            return handler

        return decorator

    def ws(self, path):
        if path.endswith("/"):
            path = path[:-1]

        def decorator(handler):
            self._add_ws_route(
                path,
                handler,
            )
            return handler

        return decorator

    def _add_http_route(self, path, methods, handler):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._http_routes.append((re.compile(path_re), methods, handler))
        return handler

    def _add_ws_route(self, path, handler):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._ws_routes.append(
            (
                re.compile(path_re),
                handler,
            )
        )
        return handler

    # Match path to handler + exctract slugs
    def _match_http(self, scope):
        path_info = scope.path
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        request_method = scope.method
        for path, methods, handler in self._http_routes:
            # Skip if invalid method
            if request_method not in methods:
                continue
            m = path.match(path_info)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {"path_params": path_params, "handler": handler}

    def _match_ws(self, scope):
        path_info = scope.path
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        for (
            path,
            handler,
        ) in self._ws_routes:
            m = path.match(path_info)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {
                    "path_params": path_params,
                    "handler": handler,
                }

    # Parsers
    def _parse_qs(self, scope):
        query_string = scope.query_string
        if not query_string:
            return {}
        parsed = parse_qs(query_string)
        return {
            key: value[0] if len(value) == 1 else value for key, value in parsed.items()
        }

    def _parse_headers(self, scope):
        headers = dict()
        for header in scope.headers.items():
            headers[header[0]] = header[1]
        return headers

    # Body readers
    async def _read_http_body(self, proto):
        msg = await proto()
        return bytes(msg)

    def _validate_http_request(self, request: Request, compiled_request_schema):
        request_validation_errors = []
        # Validate request is a json
        try:
            request.json
        except ValueError:
            return ["Invalid request body"]
        # Validate request json
        if compiled_request_schema:
            for error in compiled_request_schema.iter_errors(request.json):
                request_validation_errors.append(error.message)
        return request_validation_errors

    def _validate_http_response(self, response: JSONResponse, compiled_response_schema):
        response_validation_errors = []
        # Validate request json
        if compiled_response_schema:
            for error in compiled_response_schema.iter_errors(response.data):
                response_validation_errors.append(error.message)
        return response_validation_errors

    async def _http_response(self, response, proto):
        proto.response_str(
            status=response.status, headers=response.headers, body=response.body
        )

    async def _http_handler(self, scope, proto):
        # Match to http router and extract slugs
        match = self._match_http(scope)
        if match is None:
            response = JSONResponse(status=404, data={"message": "Resource not found"})
            await self._http_response(response, proto)
            return

        path_params = match["path_params"]
        handler = match["handler"]

        # Parse request dependencies
        headers = self._parse_headers(scope)
        query_params = self._parse_qs(scope)
        body = await self._read_http_body(proto)

        # Prepare Request object
        path_info = scope.path
        request_method = scope.method

        request = Request()
        request.proto = proto
        request.headers = headers
        request.method = request_method
        request.path = path_info
        request.slugs = path_params
        request.query = query_params
        request.body = body

        # Prepare Response
        if iscoroutinefunction(handler):
            handler_response = await handler(request)
        else:
            # Run sync function in the threadpool
            sync_future = self._loop.run_in_executor(None, handler, request)
            # Await the result without blocking the main event loop
            handler_response = await sync_future

        # Check JSONResponse is returned
        if not isinstance(handler_response, JSONResponse):
            raise ValueError("Invalid response object")

        # Flow success
        await self._http_response(handler_response, proto)

    async def _ws_handler(self, scope, proto):
        # Match to ws router and extract slugs
        match = self._match_ws(scope)
        if match is None:
            proto.close(404)
            return

        path_params = match["path_params"]
        handler = match["handler"]

        # Parse ws connection dependencies
        headers = self._parse_headers(scope)
        query_params = self._parse_qs(scope)

        # prepare websocket connection object
        connection = WebSocketConnection()
        connection.proto = proto
        connection.headers = headers
        connection.proto = proto
        connection.query = query_params
        connection.slugs = path_params
        await handler(connection)

    async def __call__(self, scope, proto):
        if scope.proto == "http":
            await self._http_handler(scope, proto)
        elif scope.proto == "ws":
            await self._ws_handler(scope, proto)
