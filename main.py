from starlette.applications import Starlette
from starlette.requests import Request

from starlette.routing import Mount, Host, Route
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.sse import SseServerTransport
from starlette.types import Receive, Scope, Send
from auth import JwtAuthTransport
import uvicorn
import os
from dotenv import load_dotenv
from configs.ragflow import ragflow
from services.chat_assistant import create_chat_session
from services.dataset import create_initial_dataset, get_dataset_by_name
from settings import settings
import json

global_session = {}
load_dotenv()


def get_transport():
    try:
        if settings.enable_auth:
            return JwtAuthTransport("/messages/")
        return SseServerTransport("/messages/")
    except Exception as e:
        print(f"Warning: Error initializing transport: {e}")
        return SseServerTransport("/messages/")  # Fallback to SSE transport


mcp = FastMCP("Ragflow MCP")
transport = get_transport()


async def handle_sse(request):
    try:
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp._mcp_server.run(
                streams[0],
                streams[1],
                mcp._mcp_server.create_initialization_options(),
            )
    except Exception as e:
        print(f"Error in handle_sse: {e}")
        raise


def wrap_handle_post_message(scope: Scope,
                             receive: Receive,
                             send: Send):
    print("scope", scope.get("user_id", "World"))
    print("receive", receive)
    print("send", send)
    request = Request(scope, receive)
    print("request", request.get("headers"))
    user = request.get("headers")
    session_id_param = request.query_params.get("session_id")
    global_session[session_id_param] = user
    scope['user_id'] = "abc"
    return transport.handle_post_message(scope, receive, send)


app = Starlette(
    routes=[
        Route('/sse/', endpoint=handle_sse),
        Mount("/messages/", app=wrap_handle_post_message)
    ]
)


@mcp.tool()
def hello(ctx: Context) -> str:
    """Returns a simple greeting with user ID."""

    session_id = ctx.get("session_id", "World")
    print("session_id", session_id)
    print("ctx", ctx.get("user_id", "World"))
    return f"Hello, {ctx.get('user_id', 'World')}!"


@mcp.tool()
def get_ragflow_datasets() -> str:
    try:
        datasets = ragflow.list_datasets()
        return datasets
    except Exception as e:
        return f"Error fetching datasets: {str(e)}"


@mcp.tool()
def create_rag(name: str) -> str:
    """Creates a initial knowledge base and dataset for the user.

    Args:
        name (str): The name of the dataset to create

    Returns:
        str: Response from the API indicating success or failure
    """
    existed_datasets = get_dataset_by_name(name)
    if len(existed_datasets) > 0:
        return f"Dataset '{name}' already exists"
    try:
        response = create_initial_dataset(name)
        return f"Successfully created dataset '{name}': {response.id}"
    except Exception as e:
        return f"Failed to create dataset: {str(e)}"


@mcp.tool()
def upload_rag(dataset_name: str, display_names: list[str], blobs: list[str]) -> str:
    """Uploads documents and provide more knowledge base for the dataset.

    Args:
        dataset_name (str): The name of the dataset to upload documents to
        display_names (list[str]): List of display names for the documents
        blobs (list[str]): List of document contents as strings

    Returns:
        str: Response from the API indicating success or failure
    """
    try:
        print("dataset_name", dataset_name)
        dataset = ragflow.get_dataset(name=dataset_name)

        documents = []
        for display_name, blob in zip(display_names, blobs):
            documents.append({
                "display_name": display_name,
                "blob": blob
            })

        # Upload documents
        response = dataset.upload_documents(documents)

        # Get document IDs
        doc_info = []
        for doc in response:
            dataset.async_parse_documents([doc.id])
            doc_info.append({
                "name": doc.display_name if hasattr(doc, 'display_name') else display_names[0],
                "id": doc.id
            })

        #training 

        return {
            "status": "success",
            "message": f"Successfully uploaded {len(documents)} documents",
            "dataset": dataset_name,
            "documents": doc_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def query_rag(dataset_name: str, query: str) -> str:
    """Returns the answer from the knowledge base.

    Returns:
        content: The answer from the knowledge base,
        source: The source of the answer
    """
    try:
        session = create_chat_session(dataset_name)
        response = session.ask(question=query)
        return response
    except Exception as e:
        return f"Error querying dataset: {str(e)}"


# or dynamically mount as host
app.router.routes.append(Host('mcp.acme.corp', app=app))

if __name__ == "__main__":
    # Run the server with Uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
