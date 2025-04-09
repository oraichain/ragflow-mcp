import base64
from contextlib import asynccontextmanager

from starlette.types import Scope, Receive, Send
from starlette.exceptions import HTTPException

from mcp.server.sse import SseServerTransport


class JwtAuthTransport(SseServerTransport):
    """
    Example basic auth implementation of SSE server transport.
    """

    def __init__(self, endpoint: str):
        super().__init__(endpoint)

    @asynccontextmanager
    async def connect_sse(self, scope: Scope, receive: Receive, send: Send):
        auth_header = dict(scope["headers"]).get(b'authorization', b'')
        print("auth_header", auth_header)
        if not auth_header:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # global_session[auth_header] = {}
        async with super().connect_sse(scope, receive, send) as streams:
            # get session from global_session
            print("global_session", streams)
            yield streams
