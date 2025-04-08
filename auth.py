import base64
from contextlib import asynccontextmanager

from starlette.types import Scope, Receive, Send
from starlette.exceptions import HTTPException

from mcp.server.sse import SseServerTransport


class JwtAuthTransport(SseServerTransport):
    """
    Example basic auth implementation of SSE server transport.
    """

    def __init__(self, endpoint: str, access_token: str):
        super().__init__(endpoint)
        self.expected_header = b"Bearer " + access_token

    @asynccontextmanager
    async def connect_sse(self, scope: Scope, receive: Receive, send: Send):
        auth_header = dict(scope["headers"]).get(b'authorization', b'')
        if not auth_header:
            raise HTTPException(status_code=401, detail="Unauthorized")
        async with super().connect_sse(scope, receive, send) as streams:
            yield streams
