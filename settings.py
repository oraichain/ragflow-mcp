# app/config.py
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    ragflow_api_key: str = os.getenv("RAGFLOW_API_KEY", "")
    ragflow_base_url: str = os.getenv(
        "RAGFLOW_BASE_URL", "")
    model_name: str = os.getenv("MODEL_NAME", "")

    class Config:
        # If you don't use .env file, pydantic can read directly from environment variables
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore extra fields from environment


settings = Settings()
# Example usage (optional, just for demonstration)
if __name__ == "__main__":
    print(f"RAGFLOW API Key: {settings.ragflow_api_key}")
    print(f"RAGFLOW Base URL: {settings.ragflow_base_url}")
