from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AgroMind API"
    use_mock: bool = True
    request_timeout: int = 30

    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""

    vision_provider: str = ""
    vision_api_key: str = ""
    vision_model: str = ""
    vision_base_url: str = ""

    rag_service_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
