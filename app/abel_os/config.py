from pydantic_settings import BaseSettings, SettingsConfigDict

from abel_os.schemas import MobileMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ABEL_", case_sensitive=False)

    app_name: str = "ABEL OS+"
    environment: str = "dev"
    mobile_mode: MobileMode = MobileMode.RECOMMEND_ONLY
    default_confidence_threshold: float = 0.75
    realtime_soft_deadline_ms: int = 350
    realtime_hard_deadline_ms: int = 1500


settings = Settings()
