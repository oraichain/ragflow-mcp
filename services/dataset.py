import json
from configs.ragflow import ragflow
from configs.logger import get_logger

logger = get_logger(__name__)


def get_dataset_by_name(user_id: str):
    try:
        datasets = ragflow.list_datasets(name=user_id)
        return datasets
    except Exception as e:
        logger.error(f"Error getting dataset by name {user_id}: {e}")
        return []


def create_initial_dataset(user_id: str):
    existed_datas = get_dataset_by_name(user_id)
    if len(existed_datas) > 0:
        return existed_datas[0]
    dataset = ragflow.create_dataset(name=user_id)
    documents = dataset.upload_documents([{
        "display_name": "base_knowledge.txt",
        "blob": "You are a helpful assistant that can answer questions about the user's data."
    }])
    document_ids = [doc.id for doc in documents]
    dataset.async_parse_documents(document_ids)
    return dataset


def upload_documents_to_dataset(dataset_name: str, display_names: list[str], blobs: list[str]) -> str:
    """Uploads documents to a RAGFlow dataset.

    Args:
        dataset_name (str): The name of the dataset to upload documents to
        display_names (list[str]): List of display names for the documents
        blobs (list[str]): List of document contents as strings

    Returns:
        str: Response from the API indicating success or failure
    """
    try:
        # Get the dataset object using dataset name
        dataset = ragflow.get_dataset(name=dataset_name)

        # Prepare documents list
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
            doc_info.append({
                "name": doc.display_name if hasattr(doc, 'display_name') else display_names[0],
                "id": doc.id
            })

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


def list_documents_in_dataset(dataset_name: str, keywords: str = None) -> str:
    """Lists documents in a RAGFlow dataset with optional keyword filtering.

    Args:
        dataset_name (str): The name of the dataset to list documents from
        keywords (str, optional): Keywords to filter documents. Defaults to None.

    Returns:
        str: List of documents matching the criteria
    """
    try:
        # Get the dataset object
        dataset = ragflow.get_dataset(name=dataset_name)

        # List documents with optional keyword filter
        documents = dataset.list_documents(keywords=keywords)

        # Format document information
        doc_list = []
        for doc in documents:
            doc_list.append({
                "id": doc.id,
                "name": doc.display_name if hasattr(doc, 'display_name') else "Unknown",
                "status": "listed"
            })

        return {
            "status": "success",
            "message": f"Found {len(doc_list)} documents",
            "dataset": dataset_name,
            "documents": doc_list
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def parse_documents_in_dataset(dataset_name: str, document_ids: list[str]) -> str:
    """Initiates async parsing of documents in a RAGFlow dataset.

    Args:
        dataset_name (str): The name of the dataset containing the documents
        document_ids (list[str]): List of document IDs to parse

    Returns:
        str: Response indicating parsing initiation status
    """
    try:
        # Get the dataset object
        dataset = ragflow.get_dataset(name=dataset_name)

        # Initiate async parsing
        dataset.async_parse_documents(document_ids)

        return {
            "status": "success",
            "message": "Async document parsing initiated",
            "dataset": dataset_name,
            "document_count": len(document_ids),
            "document_ids": document_ids
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
