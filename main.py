from starlette.applications import Starlette
from starlette.routing import Mount, Host
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from auth import JwtAuthTransport
import uvicorn
import os
from dotenv import load_dotenv
from configs.ragflow import ragflow

load_dotenv()

mcp = FastMCP("Ragflow MCP")
transport = JwtAuthTransport(
    "/messages/") if os.getenv("AUTH_ENABLED") == "true" else SseServerTransport("/messages/")


async def handle_sse(request):
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp._mcp_server.run(
            streams[0],
            streams[1],
            mcp._mcp_server.create_initialization_options(),
        )

app = Starlette(
    routes=[
        Mount('/sse/', app=handle_sse),
        Mount("/messages/", app=transport.handle_post_message)
    ]
)


@mcp.tool()
def hello() -> str:
    """Returns a simple greeting."""
    return "Hello, World!"


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


@mcp.tool()
def upload_documents_to_dataset(dataset_id: str, file_paths: list[str]) -> str:
    """Uploads documents to a RAGFlow dataset.

    Args:
        dataset_id (str): The ID of the dataset to upload documents to
        file_paths (list[str]): List of file paths to upload

    Returns:
        str: Response from the API indicating success or failure
    """
    try:
        # Upload each file to the dataset
        responses = []
        for file_path in file_paths:
            with open(file_path, 'rb') as f:
                response = ragflow.upload_document(
                    dataset_id=dataset_id,
                    file=f
                )
                responses.append(response)

        return f"Successfully uploaded {len(responses)} documents: {responses}"
    except Exception as e:
        return f"Failed to upload documents: {str(e)}"


@mcp.tool()
def list_datasets(
    page: int = 1,
    page_size: int = 30,
    orderby: str = "create_time",
    desc: bool = True,
    name: str = None,
    dataset_id: str = None
) -> str:
    """Lists datasets with filtering options.
    
    Args:
        page (int, optional): Page number for pagination. Defaults to 1.
        page_size (int, optional): Number of items per page. Defaults to 30.
        orderby (str, optional): Field to sort by ('create_time' or 'update_time'). Defaults to 'create_time'.
        desc (bool, optional): Sort in descending order if True. Defaults to True.
        name (str, optional): Filter by dataset name. Defaults to None.
        dataset_id (str, optional): Filter by dataset ID. Defaults to None.
    
    Returns:
        str: List of datasets matching the criteria
    """
    try:
        # Validate orderby parameter
        if orderby not in ["create_time", "update_time"]:
            return "Error: orderby must be either 'create_time' or 'update_time'"

        # Build query parameters
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc
        }
        
        # Add optional filters if provided
        if name:
            params["name"] = name
        if dataset_id:
            params["id"] = dataset_id

        # Get datasets with filters
        datasets = ragflow.list_datasets(**params)
        return f"Successfully retrieved datasets: {datasets}"
    except Exception as e:
        return f"Failed to list datasets: {str(e)}"


# or dynamically mount as host
app.router.routes.append(Host('mcp.acme.corp', app=app))

if __name__ == "__main__":
    # Run the server with Uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
