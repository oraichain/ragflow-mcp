from settings import settings
from ragflow_sdk import RAGFlow

ragflow = RAGFlow(
    api_key=settings.ragflow_api_key,
    base_url=settings.ragflow_base_url
)
