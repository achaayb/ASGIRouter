import re
from asyncio import get_event_loop, iscoroutinefunction
from urllib.parse import parse_qs

from pycoreapi.connection import WebSocketConnection
from pycoreapi.request import Request
from pycoreapi.response import JSONResponse
from pycoreapi.utils import is_extra_installed

import json


pydantic_installed = is_extra_installed("pydantic")
if pydantic_installed:
    from pydantic import BaseModel, ValidationError

class CoreAPI:
    def __init__(self: "CoreAPI"):
        self._http_routes = []
        self._ws_routes = []
        self._loop = get_event_loop()

    # Exposed decorators
    def route(self, path, methods=None, request_validator=None):

        # Check if Pydantic is installed if a request validator is provided
        if request_validator and not pydantic_installed:
            raise Exception(
                "request_validator requires Pydantic. Install it using: pip3 install pycoreapy[pydantic]"
            )

        # Check if the provided request validator is a subclass of BaseModel
        if request_validator and not issubclass(request_validator, BaseModel):
            raise Exception("request_validator must be a subclass of pydantic BaseModel")

        if methods is None:
            methods = ["GET"]

        if path.endswith("/"):
            path = path[:-1]

        def decorator(handler):
            self._add_http_route(path, methods, handler, request_validator)
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

    def _add_http_route(self, path, methods, handler, request_validator):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._http_routes.append((re.compile(path_re), methods, handler, request_validator))
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
        for path, methods, handler, request_validator in self._http_routes:
            # Skip if invalid method
            if request_method not in methods:
                continue
            m = path.match(path_info)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {"path_params": path_params, "handler": handler, "request_validator": request_validator}

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
    
    # Validate and parse
    async def _validate(self, request, request_validator, proto):
        # Overwrites request object
        try:
            body_headers_query_dict = request.dict_minified
            validated_request = request_validator(
                **body_headers_query_dict
            )
            request.headers = validated_request.headers.dict()
            request.body = validated_request.body.dict()
            request.query = validated_request.query.dict()
        except json.JSONDecodeError as e:
            # Body to json failed
            response = JSONResponse(
                status=400,
                data={"error": "Parsing Error", "details": "Invalid Json body"}
            )
            await self._http_response(response, proto)
        except ValidationError as e:
            # Handle validation errors
            response = JSONResponse(
                status=400,
                data={"error": "Validation Error", "details": e.errors()}
            )
            await self._http_response(response, proto)


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
        request_validator = match["request_validator"]

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

        # Validate request
        # Warning: overwrites initial request object
        if request_validator and pydantic_installed:
            await self._validate(request, request_validator, proto)

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
