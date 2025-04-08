from ragflow_sdk import RAGFlow
from starlette.applications import Starlette
from starlette.routing import Mount, Host
from mcp.server.fastmcp import FastMCP
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

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

print("RAGFLOW_API_KEY", os.getenv("RAGFLOW_API_KEY"))

ragflow = RAGFlow(
    api_key=os.getenv("RAGFLOW_API_KEY"),
    base_url=os.getenv("RAGFLOW_BASE_URL")
)

@mcp.tool()
def get_ragflow_datasets() -> str:
    datasets = ragflow.list_datasets()
    
    """Returns an answer from RAGFlow."""
    return datasets

@mcp.tool()
def create_ragflow_dataset(name: str) -> str:
    """Creates a new dataset in RAGFlow.
    
    Args:
        name (str): The name of the dataset to create
        
    Returns:
        str: Response from the API indicating success or failure
    """
    try:
        response = ragflow.create_dataset(name=name)
        return f"Successfully created dataset '{name}': {response}"
    except Exception as e:
        return f"Failed to create dataset: {str(e)}"

# or dynamically mount as host
app.router.routes.append(Host('mcp.acme.corp', app=mcp.sse_app()))

if __name__ == "__main__":
    # Run the server with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)