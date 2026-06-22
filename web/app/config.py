import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load repo-root .env first, then web/.env for local gateway-specific overrides.
_WEB_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _WEB_DIR.parent
_ROOT_ENV_FILE = _REPO_ROOT / ".env"
_ENV_FILE = _WEB_DIR / ".env"

load_dotenv(_ROOT_ENV_FILE, override=False)
load_dotenv(_ENV_FILE, override=True)


class Settings(BaseSettings):
    app_name: str = "TerraMind API"
    # Dev default: use product RAG on 8001 (override with USE_MOCK=true for demos)
    use_mock: bool = False
    request_timeout: int = 90

    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""

    vision_provider: str = ""
    vision_api_key: str = ""
    vision_model: str = "gpt-4o-mini"
    vision_base_url: str = ""

    rag_service_url: str = "http://localhost:8001/query"

    model_config = SettingsConfigDict(
        env_file=(str(_ROOT_ENV_FILE), str(_ENV_FILE)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def apply_openai_defaults(self):
        if not self.vision_api_key:
            key = os.getenv("OPENAI_API_KEY", "").strip()
            if key:
                self.vision_api_key = key
        if self.vision_api_key and not self.vision_provider:
            self.vision_provider = "openai"
        if not self.vision_model:
            self.vision_model = "gpt-4o-mini"
        if not self.llm_model and self.llm_api_key:
            self.llm_model = "gpt-4o-mini"
        return self


settings = Settings()
