import asyncio
import json

import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Host, Mount, Route
from starlette.types import Receive, Scope, Send

from auth import JwtAuthTransport
from configs.ragflow import ragflow
from services.chat_assistant import ask_ragflow
from services.dataset import create_initial_dataset, get_dataset_by_name
from settings import settings

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


async def wrap_handle_post_message(scope: Scope, receive: Receive, send: Send):
    temp_request = Request(scope, receive)
    authorization = temp_request.headers.get("authorization")
    # ---- Start modify body ----
    original_body_bytes = b""
    original_receive = receive
    more_body = True
    while more_body:
        message = await original_receive()
        print(f"Received message: {message}")
        if message["type"] == "http.request":
            original_body_bytes += message.get("body", b"")
            more_body = message.get("more_body", False)
        elif message["type"] == "http.disconnect":
            print("Client disconnected while reading body")
            return
        else:
            pass

    modified_body_bytes = original_body_bytes
    try:
        # Parse JSON
        data = json.loads(original_body_bytes.decode("utf-8"))
        if "params" in data and "arguments" in data["params"]:
            if settings.enable_auth:
                data["params"]["arguments"]["dataset_name"] = authorization
        modified_body_bytes = json.dumps(data).encode("utf-8")
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse request body as JSON: {e}")

    except Exception as e:
        print(f"Error during body modification: {e}")
    _receive_called = False

    async def modified_receive():
        nonlocal _receive_called
        if not _receive_called:
            _receive_called = True
            return {
                "type": "http.request",
                "body": modified_body_bytes,
                "more_body": False,
            }
        else:
            await asyncio.sleep(3600)
            return {"type": "http.disconnect"}

    return await transport.handle_post_message(scope, modified_receive, send)


app = Starlette(
    routes=[
        Route("/sse/", endpoint=handle_sse),
        Mount("/messages/", app=wrap_handle_post_message),
    ]
)


# @mcp.tool()
# def get_ragflow_datasets() -> str:
#     try:
#         datasets = ragflow.list_datasets()
#         return datasets
#     except Exception as e:
#         return f"Error fetching datasets: {str(e)}"

# @mcp.tool()
# def create_rag(name: str) -> str:
#     """Creates a initial knowledge base and dataset for the user.

#     Args:
#         name (str): The name of the dataset to create,

#     Returns:
#         str: Response from the API indicating success or failure
#     """
#     existed_datasets = get_dataset_by_name(name)
#     if len(existed_datasets) > 0:
#         return f"Dataset '{name}' already exists"
#     try:
#         response = create_initial_dataset(name)
#         return f"Successfully created dataset '{name}': {response.id}"
#     except Exception as e:
#         return f"Failed to create dataset: {str(e)}"

dataset_name = "Conversation Memories"


@mcp.tool()
def save_recall_memory(memory: str, conversation_id: str) -> str:
    """Save a memory to the database for later semantic retrieval.

    Args:
        memory (str): The memory to be saved.
        conversation_id (str): The conversation id to be saved.

    Returns:
        str: The saved memory.
    """
    try:
        dataset = ragflow.get_dataset(name=dataset_name)

        # create a new document for memory: memory: str -> dict(display_name: The file name to display in the dataset, blob: The binary content of the file to upload.)
        document = {
            "display_name": conversation_id + ".txt",
            "blob": memory.encode("utf-8"),
        }

        # upload the document to the dataset
        documents = dataset.upload_documents([document])

        document = documents[0]

        # parse document to memory
        dataset.async_parse_documents([document.id])

        # set metadata
        document.update({"meta_fields": {"name": conversation_id}})

        return memory
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def search_memory(query: str, conversation_id: str) -> str:
    """Search for memories in the database based on semantic similarity.

    Args:
        query (str): The search query.
        conversation_id (str): The conversation id to be saved.
        top_k (int): The number of results to return.

    Returns:
        list[str]: A list of relevant memories.
    """
    try:
        dataset = ragflow.get_dataset(name=dataset_name)

        # search for the memory
        results = ragflow.retrieve(
            dataset_ids=[dataset.id],
            document_ids=None,
            question=conversation_id + " " + query,
            page=1,
            page_size=3,
            similarity_threshold=0.5,
            vector_similarity_weight=0.5,
            top_k=5,
            rerank_id=None,
            keyword=False,
        )

        print(results)

        return results

    except Exception as e:
        return f"Error querying dataset: {str(e)}"


# or dynamically mount as host
app.router.routes.append(Host("mcp.acme.corp", app=app))

if __name__ == "__main__":
    # Run the server with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
