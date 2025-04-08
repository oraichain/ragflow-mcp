from starlette.applications import Starlette
from starlette.routing import Mount, Host
from mcp.server.fastmcp import FastMCP
import uvicorn


mcp = FastMCP("My App")

# Define a simple "hello" tool
@mcp.tool()
def hello() -> str:
    """Returns a simple greeting."""
    return "Hello, World!"

# Mount the SSE server to the existing ASGI server
app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

# or dynamically mount as host
app.router.routes.append(Host('mcp.acme.corp', app=mcp.sse_app()))

if __name__ == "__main__":
    # Run the server with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)